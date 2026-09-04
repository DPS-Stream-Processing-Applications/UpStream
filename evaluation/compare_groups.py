#!/usr/bin/env python3
"""
compare_groups.py

Compare two GROUPS of experiment runs (parquet files with columns:
metric, timestamp, value, pod), stored in a directory. Every file whose
name contains PATTERN_A is grouped together, every file whose name
contains PATTERN_B is grouped together, and for every metric shared by
both groups the script plots the group mean over time as a line with a
shaded +/- 1 standard deviation band, so the two groups can be compared
run-to-run-consistency and all.

Runs within a group don't need identical lengths or timestamps: each
run is put on a "seconds since its own start" axis, and its real,
un-interpolated samples are snapped into discrete time buckets (bucket
width = each metric's own sampling interval, auto-inferred from the
data). The mean/std at each bucket is computed only from the actual
values that landed there -- no synthetic/interpolated points are ever
created. Only the time range covered by every run in a group is used,
so mean/std aren't skewed by a run that ended early.

Metrics reported per-pod (e.g. task_manager_cpu, task_manager_memory)
are first averaged across pods within each individual run, so runs with
a different number of task managers stay comparable.

Usage
-----
    python compare_groups.py DIRECTORY PATTERN_A PATTERN_B [--out-dir OUT_DIR] [--bin-seconds SECONDS]

Example
-------
    python compare_groups.py ./runs "8_tm" "64_tm" --out-dir comparison_plots

    -> groups every *.parquet file in ./runs whose filename contains
       "8_tm" into group A, every file containing "64_tm" into group B,
       and plots mean +/- std per metric for each group.

Output
------
One PNG per metric (saved to --out-dir, default "./comparison_plots"),
plus a combined "all_metrics_overview.png" grid figure.
"""

import argparse
import math
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

COLOR_A = "#013261"
COLOR_B = "#f39301"


# ----------------------------------------------------------------------
# File discovery / loading
# ----------------------------------------------------------------------


def find_group_files(directory: Path, pattern: str) -> list[Path]:
    """All .parquet files directly under `directory` whose filename
    contains `pattern` (case-sensitive substring match)."""
    return sorted(p for p in directory.glob("*.parquet") if pattern in p.name)


def load_run(path: Path) -> pd.DataFrame:
    """Load a run parquet file and add a relative-time column (seconds
    since the first timestamp in that run)."""
    df = pd.read_parquet(path)
    df = df.sort_values("timestamp").copy()
    t0 = df["timestamp"].min()
    df["t_seconds"] = (df["timestamp"] - t0).dt.total_seconds()
    return df


def series_for_metric(df: pd.DataFrame, metric: str) -> pd.DataFrame:
    """Return a (t_seconds, value) series for a metric within a single
    run, averaging across pods at each timestamp when the metric has
    multiple pods (e.g. one row per task manager)."""
    sub = df[df["metric"] == metric]
    if sub["pod"].nunique() > 1:
        sub = sub.groupby("timestamp", as_index=False).agg(
            value=("value", "mean"), t_seconds=("t_seconds", "first")
        )
    return sub[["t_seconds", "value"]].sort_values("t_seconds")


# ----------------------------------------------------------------------
# Group aggregation
# ----------------------------------------------------------------------


def infer_bin_seconds(per_run_series: list[pd.DataFrame]) -> float:
    """Infer a sampling interval (in seconds) for a metric from the
    actual gaps between consecutive samples, so raw samples can be
    grouped into discrete time buckets without any interpolation."""
    diffs = []
    for s in per_run_series:
        d = np.diff(s["t_seconds"].values)
        d = d[d > 0]
        if len(d):
            diffs.append(np.median(d))
    if not diffs:
        return 15.0  # fallback, shouldn't normally be hit
    return float(np.median(diffs))


def group_mean_std(
    runs: list[pd.DataFrame], metric: str, bin_seconds: float | None = None
):
    """Given several runs (each a full dataframe for one file), compute
    the mean and std of `metric` across those runs at each discrete
    sample time -- no interpolation. Each run's real (t_seconds, value)
    samples are snapped to the nearest time bucket (bucket width =
    `bin_seconds`, auto-inferred from the data's own sampling interval
    if not given) and the mean/std at each bucket is computed only from
    the actual values that landed there. Only the time range common to
    *all* runs that contain this metric is used, so the mean/std are not
    skewed by runs that ended early.

    Returns (bucket_times, mean, std, n_runs_used) or None if no run has
    the metric.
    """
    per_run_series = []
    max_common_t = None
    for df in runs:
        s = series_for_metric(df, metric)
        if s.empty:
            continue
        per_run_series.append(s)
        run_max = s["t_seconds"].max()
        max_common_t = run_max if max_common_t is None else min(max_common_t, run_max)

    if not per_run_series or max_common_t is None or max_common_t <= 0:
        return None

    if bin_seconds is None:
        bin_seconds = infer_bin_seconds(per_run_series)

    # Collect every run's raw, real samples (restricted to the time range
    # every run in the group covers) and snap each to the nearest bucket.
    all_points = pd.concat(
        [s[s["t_seconds"] <= max_common_t] for s in per_run_series],
        ignore_index=True,
    )
    all_points["t_bucket"] = (
        all_points["t_seconds"] / bin_seconds
    ).round() * bin_seconds

    grouped = (
        all_points.groupby("t_bucket")["value"]
        .agg(mean="mean", std="std", count="count")
        .reset_index()
        .sort_values("t_bucket")
    )
    grouped["std"] = grouped["std"].fillna(
        0.0
    )  # a bucket with a single sample has no spread

    return (
        grouped["t_bucket"].to_numpy(),
        grouped["mean"].to_numpy(),
        grouped["std"].to_numpy(),
        len(per_run_series),
    )


# ----------------------------------------------------------------------
# Plotting
# ----------------------------------------------------------------------


def plot_metric(ax, metric, agg_a, agg_b, label_a, label_b, per_pod_note=False):
    if agg_a is not None:
        grid_a, mean_a, std_a, n_a = agg_a
        ax.plot(
            grid_a, mean_a, color=COLOR_A, linewidth=1.6, label=f"{label_a} (n={n_a})"
        )
        ax.fill_between(
            grid_a, mean_a - std_a, mean_a + std_a, color=COLOR_A, alpha=0.2
        )
    if agg_b is not None:
        grid_b, mean_b, std_b, n_b = agg_b
        ax.plot(
            grid_b, mean_b, color=COLOR_B, linewidth=1.6, label=f"{label_b} (n={n_b})"
        )
        ax.fill_between(
            grid_b, mean_b - std_b, mean_b + std_b, color=COLOR_B, alpha=0.2
        )

    title = metric.replace("_", " ")
    if per_pod_note:
        title += " (avg across pods)"
    ax.set_title(title, fontsize=11, fontweight="bold")
    ax.set_xlabel("Time since run start (s)")
    ax.set_ylabel("value")
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8)


def main():
    parser = argparse.ArgumentParser(
        description="Compare two groups of experiment runs (mean +/- std per metric)."
    )
    parser.add_argument("directory", help="Directory to search for .parquet run files")
    parser.add_argument(
        "pattern_a", help="Substring identifying files that belong to group A"
    )
    parser.add_argument(
        "pattern_b", help="Substring identifying files that belong to group B"
    )
    parser.add_argument(
        "--out-dir", default="comparison_plots", help="Directory to save plots into"
    )
    parser.add_argument(
        "--bin-seconds",
        type=float,
        default=None,
        help="Width (in seconds) of the discrete time buckets samples are grouped into. "
        "If omitted, it's auto-inferred per metric from that metric's own sampling interval.",
    )
    args = parser.parse_args()

    directory = Path(args.directory)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Use the target directory's name (last path component) as a filename
    # prefix so plots from different input directories don't collide/overwrite
    # each other when saved into the same --out-dir.
    dir_prefix = directory.resolve().name or "root"

    files_a = find_group_files(directory, args.pattern_a)
    files_b = find_group_files(directory, args.pattern_b)

    if not files_a:
        raise SystemExit(
            f"No .parquet files in {directory} contain pattern '{args.pattern_a}'"
        )
    if not files_b:
        raise SystemExit(
            f"No .parquet files in {directory} contain pattern '{args.pattern_b}'"
        )

    overlap = set(files_a) & set(files_b)
    if overlap:
        print(
            f"Warning: {len(overlap)} file(s) match BOTH patterns and will be counted in both groups: "
            f"{[p.name for p in overlap]}"
        )

    print(
        f"Group A ('{args.pattern_a}'): {len(files_a)} file(s) -> {[p.name for p in files_a]}"
    )
    print(
        f"Group B ('{args.pattern_b}'): {len(files_b)} file(s) -> {[p.name for p in files_b]}"
    )

    runs_a = [load_run(p) for p in files_a]
    runs_b = [load_run(p) for p in files_b]

    label_a = f"'{args.pattern_a}' group"
    label_b = f"'{args.pattern_b}' group"

    metrics_a = set().union(*(set(df["metric"].unique()) for df in runs_a))
    metrics_b = set().union(*(set(df["metric"].unique()) for df in runs_b))
    shared_metrics = sorted(metrics_a & metrics_b)

    only_a = metrics_a - metrics_b
    only_b = metrics_b - metrics_a
    if only_a:
        print(f"Note: metrics only in group A: {sorted(only_a)}")
    if only_b:
        print(f"Note: metrics only in group B: {sorted(only_b)}")
    print(f"Comparing {len(shared_metrics)} shared metrics: {shared_metrics}")

    # Individual plots
    metric_aggs = {}
    for metric in shared_metrics:
        agg_a = group_mean_std(runs_a, metric, args.bin_seconds)
        agg_b = group_mean_std(runs_b, metric, args.bin_seconds)
        metric_aggs[metric] = (agg_a, agg_b)

        per_pod = any(
            df[df["metric"] == metric]["pod"].nunique() > 1 for df in (runs_a + runs_b)
        )

        fig, ax = plt.subplots(figsize=(9, 4.5))
        plot_metric(ax, metric, agg_a, agg_b, label_a, label_b, per_pod_note=per_pod)
        fig.tight_layout()
        out_path = out_dir / f"{dir_prefix}_{metric}.png"
        fig.savefig(out_path, dpi=150)
        plt.close(fig)
        print(f"Saved {out_path}")

    # Combined overview grid
    n = len(shared_metrics)
    ncols = 2
    nrows = math.ceil(n / ncols)
    fig, axes = plt.subplots(nrows, ncols, figsize=(11, 3.6 * nrows))
    axes = axes.flatten() if n > 1 else [axes]

    for i, metric in enumerate(shared_metrics):
        agg_a, agg_b = metric_aggs[metric]
        per_pod = any(
            df[df["metric"] == metric]["pod"].nunique() > 1 for df in (runs_a + runs_b)
        )
        plot_metric(
            axes[i], metric, agg_a, agg_b, label_a, label_b, per_pod_note=per_pod
        )

    for j in range(len(shared_metrics), len(axes)):
        axes[j].axis("off")

    fig.suptitle(
        f"{label_a} (n={len(files_a)})  vs  {label_b} (n={len(files_b)})",
        fontsize=14,
        fontweight="bold",
        y=1.0,
    )
    fig.tight_layout()
    overview_path = out_dir / f"{dir_prefix}_all_metrics_overview.png"
    fig.savefig(overview_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved {overview_path}")


if __name__ == "__main__":
    main()
