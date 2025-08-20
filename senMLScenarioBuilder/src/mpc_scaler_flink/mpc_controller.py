from typing import Literal, TypeAlias

import do_mpc
import numpy as np
from do_mpc.controller import MPC
from do_mpc.model import Model
from numpy._typing import NDArray, _UnknownType
from numpy.core.multiarray import ndarray

Array3Float: TypeAlias = np.ndarray[Literal[3], np.dtype[np.float32]]


class MPCController:
    _model: Model
    _controller: MPC

    def __init__(
        self,
        target_utilisation: float = 0.8,
        target_busy_time: float = 0.8,
        target_backpressure: float = 0,
        event_horizon: int = 10,
    ):
        self.TARGET_UTILISATION = target_utilisation
        self.TARGET_BUSY_TIME = target_busy_time
        self.TARGET_BACKPRESSURE_TIME = target_backpressure
        self.EVENT_HORIZON = event_horizon
        self._model = self._setup_model()
        self._controller = self._setup_mpc(self._model)

    def _setup_model(self):
        model_type = "discrete"
        model = do_mpc.model.Model(model_type)

        # Observed metrics
        utilisation = model.set_variable(var_type="_x", var_name="utilisation")
        backpressure_time = model.set_variable(
            var_type="_x", var_name="backpressure_time"
        )
        busy_time = model.set_variable(var_type="_x", var_name="busy_time")

        # Control
        deviation_term = model.set_variable(var_type="_u", var_name="deviation_term")

        # Define parameters to control dynamics
        ALPHA = 0.1
        BETA = 0.5
        GAMMA = 0.1

        # NOTE: Dynamics for utilisation: decrease when scaling up (deviation_term > 1), increase otherwise
        next_utilisation = (
            utilisation
            + ALPHA * (self.TARGET_UTILISATION - utilisation)
            - BETA * deviation_term
        )
        model.set_rhs("utilisation", next_utilisation)

        # NOTE: Dynamics for busy_time: similar to utilisation, decreases with scaling up
        next_busy_time = (
            busy_time
            + ALPHA * (self.TARGET_BUSY_TIME - busy_time)
            - BETA * deviation_term
        )
        model.set_rhs("busy_time", next_busy_time)

        # NOTE: Dynamics for backpressure_time: inversely related to scaling (increases when scaling down)
        next_backpressure_time = (
            backpressure_time
            + GAMMA * (self.TARGET_BACKPRESSURE_TIME - backpressure_time)
            - BETA * deviation_term
        )
        model.set_rhs("backpressure_time", next_backpressure_time)

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

        # NOTE: The objective is to minimise the deviation from the target values.
        mterm = (
            (model.x["utilisation"] - self.TARGET_UTILISATION) ** 2
            + (model.x["busy_time"] - self.TARGET_BUSY_TIME) ** 2
            + (model.x["backpressure_time"] - self.TARGET_BACKPRESSURE_TIME) ** 2
        )

        # NOTE: The `deviation_term` is reduced by a factor of 0.5 to ensure that
        # any scaling adjustments are gradual rather than extreme.
        lterm = (
            (model.x["utilisation"] - self.TARGET_UTILISATION) ** 2
            + (model.x["busy_time"] - self.TARGET_BUSY_TIME) ** 2
            + (model.x["backpressure_time"] - self.TARGET_BACKPRESSURE_TIME) ** 2
            + 0.2 * model.u["deviation_term"] ** 2
        )

        mpc.set_objective(mterm, lterm)
        mpc.set_rterm(deviation_term=0.1)

        # NOTE:
        # The cluster can at most be scaled down to 0%. (1 + `deviation_term` >= 0)
        # A `deviation_term` < -1 would lead to a negative scaling factor.
        mpc.bounds["lower", "_u", "deviation_term"] = -1

        mpc.setup()
        return mpc

    def initial_measurement(self, metrics_array: Array3Float):
        self._controller.x0 = metrics_array
        self._controller.set_initial_guess()

    def measurement_step(self, metrics_array: Array3Float) -> float:
        deviation_term: ndarray = self._controller.make_step(metrics_array)[0]
        return float(1 + deviation_term)
