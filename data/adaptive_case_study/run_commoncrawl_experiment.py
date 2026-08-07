#!/usr/bin/env python3
"""Run the adaptive-sampling case study on the Common Crawl snapshot."""

from __future__ import annotations

import argparse
from pathlib import Path

from adaptive_sampling import load_joint_counts_csv
from run_experiment import run_case_study


HERE = Path(__file__).resolve().parent


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--joint-counts",
        type=Path,
        default=HERE / "data" / "commoncrawl_joint_counts.csv",
    )
    parser.add_argument(
        "--output-dir", type=Path, default=HERE / "results" / "commoncrawl"
    )
    parser.add_argument("--trials", type=int, default=1_000)
    parser.add_argument("--seed", type=int, default=20260722)
    parser.add_argument("--tolerance", type=float, default=0.10)
    args = parser.parse_args()

    joint_counts = load_joint_counts_csv(args.joint_counts)
    comparison = run_case_study(
        population_name="Common Crawl header snapshot",
        joint_counts=joint_counts,
        output_dir=args.output_dir,
        trials=args.trials,
        seed=args.seed,
        tolerance=args.tolerance,
        measurement_objective="prevalence-oriented affected-host rate",
        input_description=(
            f"Eight joint-state counts from {args.joint_counts.name}; regenerate "
            "from domain_issue_wide with data/extract_commoncrawl_joint_counts.sql"
        ),
    )
    print(comparison[comparison.method == "adaptive"].to_string(index=False))


if __name__ == "__main__":
    main()
