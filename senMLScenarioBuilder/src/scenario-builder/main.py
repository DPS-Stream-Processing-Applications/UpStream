import argparse
import csv
import os

import matplotlib.pyplot as plt
import numpy as np


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

    duration_ms = 15 * 60 * 1000  # The duration of the entire scenario in ms (15min)
    mean = duration_ms / 2
    std_dev = (
        duration_ms / 6
    )  # sigma 6th rule to have most data within scenario interval
    timestamps = np.random.normal(loc=mean, scale=std_dev, size=row_count)

    # Clamp to [0, duration] and sort (monotonic increasing time)
    timestamps = np.clip(timestamps, 0, duration_ms)
    timestamps = np.sort(timestamps)

    # --- Plot histogram of sampled timestamps ---
    plt.hist(timestamps / 1000, bins=50, density=True, alpha=0.6, color="blue")
    plt.axvline(mean / 1000, color="red", linestyle="--", label="mean (7.5 min)")
    plt.xlabel("Time [seconds]")
    plt.ylabel("Density")
    plt.title("Gaussian-distributed event timestamps")
    plt.legend()

    base, _ = os.path.splitext(args.target_file)
    plot_file = f"{base}_scenario.png"
    plt.savefig(plot_file, dpi=150, bbox_inches="tight")
    plt.close()

    print(f"saved distribution plot at {plot_file}")

    checks = [1, 5, 7.5, 10, 14]  # minutes
    window = 60 * 1000  # 1-minute window in ms

    # Sample events per minute
    for m in checks:
        center = m * 60 * 1000
        count = np.sum(
            (timestamps >= center - window / 2) & (timestamps < center + window / 2)
        )
        print(f"Events around {m:>4} min (±0.5 min): {count}")

    base, ext = os.path.splitext(args.target_file)
    output_file = f"{base}_scenario{ext}"
    print(f"writing scenario to {output_file}")

    with open(args.target_file, "r", encoding="utf-8") as infile, open(
        output_file, "w", newline="", encoding="utf-8"
    ) as outfile:

        reader = csv.reader(infile)
        writer = csv.writer(outfile)

        header = next(reader)
        writer.writerow(header)

        for i, row in enumerate(reader):
            print(f"rows processed: {i}", end="\r", flush=True)
            if i >= len(timestamps):
                break
            row[0] = str(int(timestamps[i]))  # overwrite only first column
            writer.writerow(row)

        print()
