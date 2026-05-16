from typing import Literal, TypeAlias

import do_mpc
import numpy as np
from do_mpc.controller import MPC
from do_mpc.model import Model
from numpy.core.multiarray import ndarray

# Array type hint for the 4 metrics
Array4Float: TypeAlias = np.ndarray[Literal[4], np.dtype[np.float32]]


class MPCController:
    _model: Model
    _controller: MPC

    def __init__(
        self,
        target_busy_time: float = 0.8,
        target_idle_time: float = 0.2,
        target_backpressure: float = 0,
        target_queue_length: float = 2,
        event_horizon: int = 10,
    ):
        self.TARGET_BUSY_TIME = target_busy_time
        self.TARGET_IDLE_TIME = target_idle_time
        self.TARGET_BACKPRESSURE_TIME = target_backpressure
        self.TARGET_QUEUE_LENGTH = target_queue_length
        self.EVENT_HORIZON = event_horizon
        self._model = self._setup_model()
        self._controller = self._setup_mpc(self._model)

    def _setup_model(self):
        model_type = "discrete"
        model = do_mpc.model.Model(model_type)

        # Observed metrics (4 states)
        busy_time = model.set_variable(var_type="_x", var_name="busy_time")
        idle_time = model.set_variable(var_type="_x", var_name="idle_time")
        backpressure_time = model.set_variable(
            var_type="_x", var_name="backpressure_time"
        )
        queue_length = model.set_variable(var_type="_x", var_name="queue_length")

        # Control
        deviation_term = model.set_variable(var_type="_u", var_name="deviation_term")

        # Define parameters to control dynamics
        ALPHA = 0.1
        BETA = 0.5
        GAMMA = 0.1

        # NOTE: Dynamics for busy_time: decreases with scaling up (positive deviation)
        next_busy_time = (
            busy_time
            + ALPHA * (self.TARGET_BUSY_TIME - busy_time)
            - BETA * deviation_term
        )
        model.set_rhs("busy_time", next_busy_time)

        # NOTE: Dynamics for idle_time: increases when scaling up (more headroom)
        next_idle_time = (
            idle_time
            + ALPHA * (self.TARGET_IDLE_TIME - idle_time)
            + BETA * deviation_term
        )
        model.set_rhs("idle_time", next_idle_time)

        # NOTE: Dynamics for backpressure_time: decreases when scaling up
        next_backpressure_time = (
            backpressure_time
            + GAMMA * (self.TARGET_BACKPRESSURE_TIME - backpressure_time)
            - BETA * deviation_term
        )
        model.set_rhs("backpressure_time", next_backpressure_time)

        # NOTE: Dynamics for queue_length: decreases when scaling up
        next_queue_length = (
            queue_length
            + GAMMA * (self.TARGET_QUEUE_LENGTH - queue_length)
            - BETA * deviation_term
        )
        model.set_rhs("queue_length", next_queue_length)

        model.setup()

        return model

    def _setup_mpc(self, model):
        mpc = do_mpc.controller.MPC(model)

        mpc.set_param(
            n_horizon=self.EVENT_HORIZON,
            t_step=1,
            n_robust=1,
            state_discretization="collocation",
            collocation_type="radau",
            collocation_deg=2,
            collocation_ni=2,
            store_full_solution=True,
        )

        # Objective terms updated for the 4 states
        mterm = (
            (model.x["busy_time"] - self.TARGET_BUSY_TIME) ** 2
            + (model.x["idle_time"] - self.TARGET_IDLE_TIME) ** 2
            + (model.x["backpressure_time"] - self.TARGET_BACKPRESSURE_TIME) ** 2
            + (model.x["queue_length"] - self.TARGET_QUEUE_LENGTH) ** 2
        )

        lterm = (
            (model.x["busy_time"] - self.TARGET_BUSY_TIME) ** 2
            + (model.x["idle_time"] - self.TARGET_IDLE_TIME) ** 2
            + (model.x["backpressure_time"] - self.TARGET_BACKPRESSURE_TIME) ** 2
            + (model.x["queue_length"] - self.TARGET_QUEUE_LENGTH) ** 2
            + 0.2 * model.u["deviation_term"] ** 2
        )

        mpc.set_objective(mterm, lterm)
        mpc.set_rterm(deviation_term=0.1)

        # Cluster downscale bounds
        mpc.bounds["lower", "_u", "deviation_term"] = -1

        mpc.setup()
        return mpc

    def initial_measurement(self, metrics_array: Array4Float):
        self._controller.x0 = metrics_array
        self._controller.set_initial_guess()

    def measurement_step(self, metrics_array: Array4Float) -> float:
        deviation_term: ndarray = self._controller.make_step(metrics_array)[0]
        return float(1 + deviation_term)
