import argparse
import csv
import os

import matplotlib.pyplot as plt
import numpy as np
from numpy.typing import NDArray
from scipy.stats import truncnorm


def sample_timestamps_linear(
    row_count, scenario_duration_ms, scenario_target_file
) -> NDArray:
    t0 = 0
    t1 = scenario_duration_ms / 6
    t2 = scenario_duration_ms - t1
    t3 = scenario_duration_ms

    x = np.linspace(0, scenario_duration_ms, 10000)
    pdf = np.zeros_like(x, dtype=float)

    # Linear rise
    pdf[(x >= t0) & (x <= t1)] = (x[(x >= t0) & (x <= t1)] - t0) / (t1 - t0)
    # Plateau
    pdf[(x > t1) & (x <= t2)] = 1.0
    # Linear fall
    pdf[(x > t2) & (x <= t3)] = (t3 - x[(x > t2) & (x <= t3)]) / (t3 - t2)

    # Normalize PDF
    pdf /= np.trapezoid(pdf, x)

    # Compute CDF
    cdf = np.cumsum(pdf)
    cdf = cdf / cdf[-1]

    # Sample uniformly and invert CDF
    u = np.random.rand(row_count)
    timestamps = np.interp(u, cdf, x)

    # --- Plot histogram ---
    plt.hist(timestamps / 1000, bins=50, density=True, alpha=0.6, color="green")
    plt.xlabel("Time [seconds]")
    plt.ylabel("Density")
    plt.title("Custom linear→plateau→linear-decrease event timestamps")

    base, _ = os.path.splitext(scenario_target_file)
    plot_file = f"{base}_linear_scenario.png"
    plt.savefig(plot_file, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved distribution plot at {plot_file}")

    # --- Count events per minute around specific marks ---
    checks = [0.5, scenario_duration_ms / 2, 14]  # minutes
    window = 60 * 1000

    for m in checks:
        center = m * 60 * 1000
        count = np.sum(
            (timestamps >= center - window / 2) & (timestamps < center + window / 2)
        )
        print(f"Events around {m:>4} min (±0.5 min): {count}")

    return np.sort(timestamps)


def sample_timestamps_gaussian(
    row_count, scenario_duration_ms, scenario_target_file
) -> NDArray:
    mean = scenario_duration_ms / 2
    std_dev = (
        scenario_duration_ms / 6
    )  # sigma 6th rule to have most data within scenario interval
    # Define truncated normal (a, b are in std dev units from the mean)
    a, b = (0 - mean) / std_dev, (scenario_duration_ms - mean) / std_dev
    trunc_normal = truncnorm(a, b, loc=mean, scale=std_dev)

    # Sample only within [0, duration]
    timestamps = trunc_normal.rvs(row_count)

    # --- Plot histogram of sampled timestamps ---
    plt.hist(timestamps / 1000, bins=50, density=True, alpha=0.6, color="blue")
    plt.axvline(mean / 1000, color="red", linestyle="--", label="mean (7.5 min)")
    plt.xlabel("Time [seconds]")
    plt.ylabel("Density")
    plt.title("Gaussian-distributed event timestamps")
    plt.legend()

    base, _ = os.path.splitext(scenario_target_file)
    plot_file = f"{base}_gaussian_scenario.png"
    plt.savefig(plot_file, dpi=150, bbox_inches="tight")
    plt.close()

    print(f"saved distribution plot at {plot_file}")

    # --- Count events per minute for discrete timestamps ---

    checks = [0.5, 5, 7.5, 10, 14.5]  # minutes
    window = 60 * 1000  # 1-minute window in ms

    for m in checks:
        center = m * 60 * 1000
        count = np.sum(
            (timestamps >= center - window / 2) & (timestamps < center + window / 2)
        )
        print(f"Events around {m:>4} min (±0.5 min): {count}")

    return np.sort(timestamps)

def sample_timestamps_exponential(row_count, scenario_duration_ms, scenario_target_file) -> NDArray:
    t0 = 0
    t1 = scenario_duration_ms / 3       # 2.5 min
    t2 = scenario_duration_ms - t1   # 12.5 min
    t3 = scenario_duration_ms           # 15 min

    # Grid for piecewise PDF
    x = np.linspace(0, scenario_duration_ms, 20001)
    pdf = np.zeros_like(x, dtype=float)

    mask_rise     = (x >= t0) & (x <= t1)
    mask_plateau  = (x >  t1) & (x <= t2)
    mask_fall     = (x >  t2) & (x <= t3)

    # Exponential rise (starting near 0 and rising to H at t1)
    tau_rise = (t1 - t0) / 3.0
    rise_raw = np.exp((x[mask_rise] - t0) / tau_rise) - 1.0
    H = rise_raw[-1]  # peak value at t1

    pdf[mask_rise] = rise_raw
    pdf[mask_plateau] = H                          # plateau at peak height
    tau_fall = (t3 - t2) / 3.0
    pdf[mask_fall] = H * np.exp(-(x[mask_fall] - t2) / tau_fall)  # decay from same height

    # Normalize PDF
    area = np.trapezoid(pdf, x)
    if area <= 0:
        raise ValueError("PDF area is non-positive; check parameters.")
    pdf /= area

    # Build CDF (account for dx)
    dx = x[1] - x[0]
    cdf = np.cumsum(pdf) * dx
    cdf /= cdf[-1]

    # Inverse transform sampling
    u = np.random.rand(row_count)
    timestamps = np.interp(u, cdf, x)

    # Plot & save
    base, _ = os.path.splitext(scenario_target_file)
    plot_file = f"{base}_scenario.png"
    plt.hist(timestamps / 1000, bins=50, density=True, alpha=0.6)
    plt.xlabel("Time [seconds]")
    plt.ylabel("Density")
    plt.title("Exponential rise → plateau (at peak) → exponential decay")
    plt.savefig(plot_file, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved distribution plot at {plot_file}")

    # Event counts around key minutes (±0.5 min)
    checks = [0.5, 2.5, 7.5, 12.5, 14.5]  # minutes
    window = 60 * 1000  # 1-minute window in ms
    for m in checks:
        center = m * 60 * 1000
        count = np.sum((timestamps >= center - window/2) & (timestamps < center + window/2))
        print(f"Events around {m:>4} min (±0.5 min): {count}")

    return np.sort(timestamps)

def main():
    parser = argparse.ArgumentParser(
        description="replace the timestamps of a senML csv file with a custom scenario."
    )
    parser.add_argument("target_file", help="Path to the target file")
    parser.add_argument(
        "--scenario",
        choices=["LINEAR", "GAUSSIAN", "EXPONENTIAL"],
        help="Type of timestamp scenario to generate",
    )
    args = parser.parse_args()

    with open(args.target_file, "rb") as f:
        row_count = sum(1 for _ in f) - 1

    print(f"Number of rows: {row_count}")
    if row_count > 1 * 1000 * 1000:
        row_count = 1 * 1000 * 1000
        print(
            """The number of rows exceeds the required maximum.
            New row count: 1 000 000"""
        )

    scenario_duration_ms = (
        15 * 60 * 1000
    )  # The duration of the entire scenario in ms (15min)

    # --- Sample timestamps based on scenario ---
    match args.scenario:
        case "LINEAR":
            timestamps = sample_timestamps_linear(
                row_count, scenario_duration_ms, args.target_file
            )
        case "GAUSSIAN":
            timestamps = sample_timestamps_gaussian(
                row_count, scenario_duration_ms, args.target_file
            )
        case "EXPONENTIAL":
            timestamps = sample_timestamps_exponential(row_count, scenario_duration_ms, args.target_file)
        case _:
            print("No known scenario provided")
            exit(1)

    base, ext = os.path.splitext(args.target_file)
    output_file = f"{base}_{args.scenario.lower()}_scenario{ext}"
    print(f"writing scenario to {output_file}")

    with (
        open(args.target_file, "r", encoding="utf-8") as infile,
        open(output_file, "w", newline="", encoding="utf-8") as outfile,
    ):

        reader = csv.reader(infile, delimiter="|")
        writer = csv.writer(outfile, delimiter="|")

        header = next(reader)
        writer.writerow(header)

        for i, row in enumerate(reader):
            print(f"rows processed: {i}", end="\r", flush=True)
            if i >= len(timestamps):
                break
            row[0] = str(int(timestamps[i]))  # overwrite only first column
            writer.writerow(row)

        print()
