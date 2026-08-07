#!/usr/bin/env python3
"""Run the adaptive-sampling case study on Tranco Top-500K."""

from __future__ import annotations

import argparse
from pathlib import Path

from adaptive_sampling import load_joint_counts_csv
from run_experiment import run_case_study


HERE = Path(__file__).resolve().parent


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--joint-counts", type=Path, default=HERE / "data" / "tranco_joint_counts.csv")
    parser.add_argument("--output-dir", type=Path, default=HERE / "results" / "tranco")
    parser.add_argument("--trials", type=int, default=1_000)
    parser.add_argument("--seed", type=int, default=20260722)
    parser.add_argument("--tolerance", type=float, default=0.10)
    args = parser.parse_args()

    joint_counts = load_joint_counts_csv(args.joint_counts)
    comparison = run_case_study(
        population_name="Tranco Top-500,000",
        joint_counts=joint_counts,
        output_dir=args.output_dir,
        trials=args.trials,
        seed=args.seed,
        tolerance=args.tolerance,
        measurement_objective="impact-oriented affected-site rate",
        input_description=(
            "Eight joint-state counts read from data/tranco_joint_counts.csv; "
            "originally reconstructed from impact/cat_issues cookie/click/acao CSVs"
        ),
    )
    print(comparison[comparison.method == "adaptive"].to_string(index=False))


if __name__ == "__main__":
    main()
