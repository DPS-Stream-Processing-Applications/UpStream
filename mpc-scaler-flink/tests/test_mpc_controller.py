import json
from typing import List, Literal, Optional, TypeAlias

import do_mpc
import matplotlib.pyplot as plt
import numpy as np

from mpc_scaler_flink.mpc_controller import MPCController

Array3Float: TypeAlias = np.ndarray[Literal[3], np.dtype[np.float32]]


def setup_simulator(model):
    simulator = do_mpc.simulator.Simulator(model)

    params_simulator = {
        "integration_tool": "cvodes",
        "abstol": 1e-10,
        "reltol": 1e-10,
        "t_step": 1.0,
    }
    simulator.set_param(**params_simulator)
    simulator.setup()
    return simulator


def get_series_values(json_filename: str, series_name: str) -> Optional[List[float]]:
    with open(json_filename, "r") as f:
        time_series_data = json.load(f)

    if series_name in time_series_data:
        return [float(value) for value in time_series_data[series_name]["data"]]
    else:
        print(f"Series '{series_name}' not found in the JSON file.")
        return None


def main():
    controller = MPCController()

    utilisation_0: float = 0
    backpressure_time_0: float = 0
    busy_time_0: float = 0
    x0: Array3Float = np.array([utilisation_0, backpressure_time_0, busy_time_0])
    controller.initial_measurement(x0)

    utilisation_trajectory: List[float] = []
    backpressure_time_trajectory: List[float] = []
    busy_time_trajectory: List[float] = []
    scaling_factor_trajectory: List[float] = []

    asc_sin_values = get_series_values("test_time_series.json", "ascending_sinusoidal_series")
    sin_values = get_series_values("test_time_series.json", "sinusoidal_series")
    linear_series = get_series_values("test_time_series.json", "linear_series")
    # NOTE: If read failed test fails too.
    if asc_sin_values is None:
        return
    if sin_values is None:
        return
    if linear_series is None:
        return

    n_steps = 50
    for k in range(n_steps):
        measurement: Array3Float = np.array([sin_values[k], linear_series[k], asc_sin_values[k]])
        scaling_factor = controller.measurement_step(measurement)

        utilisation_trajectory.append(float(measurement[0]))
        backpressure_time_trajectory.append(float(measurement[1]))
        busy_time_trajectory.append(float(measurement[2]))
        scaling_factor_trajectory.append(scaling_factor)

        print(
            f"Step {k}: Utilization={measurement[0]}, Backpressure Time={measurement[1]}, Busy Time={measurement[2]}, Scaling Factor={scaling_factor}"
        )

    if not (
        utilisation_trajectory
        and backpressure_time_trajectory
        and busy_time_trajectory
        and scaling_factor_trajectory
    ):
        print("Error: One or more trajectories are empty. Check the simulation setup.")
        return

    # Plot results
    fig, ax = plt.subplots(4, sharex=True, figsize=(10, 10))

    ax[0].plot(utilisation_trajectory, label="Utilization", color="b")
    ax[0].set_ylabel("Utilization")
    ax[0].legend(loc="upper right")

    ax[1].plot(backpressure_time_trajectory, label="Backpressure Time", color="g")
    ax[1].set_ylabel("Backpressure Time")
    ax[1].legend(loc="upper right")

    ax[2].plot(busy_time_trajectory, label="Busy Time", color="purple")
    ax[2].set_ylabel("Busy Time")
    ax[2].legend(loc="upper right")

    ax[3].plot(scaling_factor_trajectory, label="Scaling Factor", color="r")
    ax[3].set_ylabel("Scaling Factor")
    ax[3].set_xlabel("Time Step")
    ax[3].legend(loc="upper right")

    plt.tight_layout()
    plt.savefig("simulation_output.png", format="png", dpi=300)


if __name__ == "__main__":
    main()
