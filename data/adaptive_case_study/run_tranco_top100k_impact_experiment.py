#!/usr/bin/env python3
"""Run adaptive sampling within a Tranco Top-100K impact target frame."""

from __future__ import annotations

import argparse
from pathlib import Path

from adaptive_sampling import load_joint_counts_csv
from run_experiment import run_case_study


HERE = Path(__file__).resolve().parent
TARGET_FRAME_SIZE = 100_000


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Estimate affected-site rates within the declared Tranco Top-100K "
            "target frame when measuring every site is infeasible."
        )
    )
    parser.add_argument("--joint-counts", type=Path, default=HERE / "data" / "tranco_top100k_joint_counts.csv")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=HERE / "results" / "tranco_top100k_impact",
    )
    parser.add_argument("--trials", type=int, default=1_000)
    parser.add_argument("--seed", type=int, default=20260722)
    parser.add_argument("--tolerance", type=float, default=0.10)
    args = parser.parse_args()

    joint_counts = load_joint_counts_csv(args.joint_counts)
    comparison = run_case_study(
        population_name="Tranco Top-100,000 impact-oriented target frame",
        joint_counts=joint_counts,
        output_dir=args.output_dir,
        trials=args.trials,
        seed=args.seed,
        tolerance=args.tolerance,
        measurement_objective="impact-oriented affected-site rate",
        input_description=(
            "Eight joint-state counts read from data/tranco_top100k_joint_counts.csv; "
            "originally reconstructed from the Tranco Top-100K prefix of the "
            "impact/cat_issues cookie/click/acao CSVs."
        ),
    )
    print(comparison[comparison.method == "adaptive"].to_string(index=False))


if __name__ == "__main__":
    main()
