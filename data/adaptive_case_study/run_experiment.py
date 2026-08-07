#!/usr/bin/env python3
"""Dataset-independent experiment runner and result writer.

This module performs no plotting. Figures are generated later from its CSV and
JSON outputs by ``plot_results.py``.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from adaptive_sampling import (
    ISSUES,
    evaluate_method,
    issue_truth_from_joint_counts,
    planned_stages,
    representative_trajectory,
    simulate_nested_counts,
    stopping_distribution,
)


METHODS = (
    "fixed_2pct",
    "fixed_4pct",
    "change_only",
    "margin_only",
    "adaptive",
)


def run_case_study(
    *,
    population_name: str,
    joint_counts,
    output_dir: Path,
    trials: int,
    seed: int,
    tolerance: float,
    input_description: str,
    measurement_objective: str = "prevalence-oriented",
) -> pd.DataFrame:
    """Run one retrospective case study and write machine-readable outputs."""
    output_dir.mkdir(parents=True, exist_ok=True)
    population_size = int(joint_counts.sum())
    stages = planned_stages(population_size)
    truth = issue_truth_from_joint_counts(joint_counts)
    counts = simulate_nested_counts(joint_counts, stages, trials, seed)

    method_frames = []
    adaptive_details = None
    for method in METHODS:
        frame, details = evaluate_method(
            method,
            counts,
            stages,
            truth,
            population_size,
            tolerance,
        )
        method_frames.append(frame)
        if method == "adaptive":
            adaptive_details = details

    comparison = pd.concat(method_frames, ignore_index=True)
    comparison.to_csv(output_dir / "method_comparison.csv", index=False)
    comparison[comparison.method == "adaptive"].to_csv(
        output_dir / "adaptive_results.csv", index=False
    )

    sensitivity_frames = []
    for sensitivity_tolerance in (0.05, 0.10, 0.20):
        frame, _ = evaluate_method(
            "adaptive",
            counts,
            stages,
            truth,
            population_size,
            sensitivity_tolerance,
        )
        frame.insert(1, "relative_tolerance", sensitivity_tolerance)
        sensitivity_frames.append(frame)
    pd.concat(sensitivity_frames, ignore_index=True).to_csv(
        output_dir / "tolerance_sensitivity.csv", index=False
    )

    if adaptive_details is None:
        raise RuntimeError("adaptive method was not evaluated")
    representative_trajectory(
        adaptive_details,
        counts,
        stages,
        truth,
        population_size,
    ).to_csv(output_dir / "representative_trajectory.csv", index=False)
    stopping_distribution(
        adaptive_details["stop_n"], stages, population_size
    ).to_csv(output_dir / "stopping_distribution.csv", index=False)

    joint_frame = pd.DataFrame(
        {"mask": range(len(joint_counts)), "domains": joint_counts}
    )
    joint_frame.to_csv(output_dir / "joint_counts_used.csv", index=False)

    metadata = {
        "population": population_name,
        "measurement_objective": measurement_objective,
        "population_size": population_size,
        "trials": trials,
        "seed": seed,
        "issues": [issue for issue, _, _ in ISSUES],
        "true_rates": dict(zip([x[0] for x in ISSUES], truth.tolist())),
        "stages": stages.tolist(),
        "stage_fractions": (stages / population_size).tolist(),
        "pilot_fraction": 0.02,
        "minimum_looks": 2,
        "relative_change_tolerance": tolerance,
        "relative_margin_tolerance": tolerance,
        "confidence_interval": (
            "Stagewise normal-approximation 95% proportion interval with "
            "finite-population correction"
        ),
        "confidence_interval_role": (
            "A familiar margin-of-error diagnostic, not a claim of "
            "sequentially simultaneous 95% coverage"
        ),
        "sampling": (
            "Nested uniform random sampling without replacement; cumulative "
            "sample size doubles at every stage"
        ),
        "simulation": (
            "Exact multivariate-hypergeometric increments over the eight joint "
            "outcome states; distributionally equivalent to random-permutation "
            "prefix sampling"
        ),
        "input_description": input_description,
        "ground_truth_policy": (
            "The full-frame affected-site rate is not passed to the stopping "
            "rule; it is used only after stopping to evaluate relative error"
        ),
    }
    (output_dir / "metadata.json").write_text(
        json.dumps(metadata, indent=2), encoding="utf-8"
    )
    return comparison
