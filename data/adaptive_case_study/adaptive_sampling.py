"""Shared implementation for the adaptive-prevalence case studies.

The operational rule uses only cumulative sample counts. Full-population
prevalence is passed only to the retrospective evaluation functions.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


ISSUES = (
    ("Cookie security", "cat_issues/cookie.csv", "High"),
    ("Clickjacking", "cat_issues/click.csv", "Medium"),
    ("CORS", "cat_issues/acao.csv", "Low"),
)

Z_95 = 1.959963984540054


def planned_stages(population_size: int, pilot_fraction: float = 0.02) -> np.ndarray:
    """Return cumulative 2%, 4%, ..., 100% sample sizes."""
    if population_size < 2:
        raise ValueError("population_size must be at least 2")
    if not 0.0 < pilot_fraction < 1.0:
        raise ValueError("pilot_fraction must be between 0 and 1")

    stages = [max(1, int(round(population_size * pilot_fraction)))]
    while stages[-1] < population_size:
        stages.append(min(2 * stages[-1], population_size))
    return np.asarray(stages, dtype=np.int64)


def load_tranco_joint_counts(data_dir: Path, population_size: int) -> np.ndarray:
    """Encode the three Tranco outcomes as counts of the eight joint states."""
    labels = np.zeros((population_size, len(ISSUES)), dtype=np.uint8)
    for issue_idx, (_, relative_path, _) in enumerate(ISSUES):
        source = data_dir / relative_path
        ranks = (
            pd.read_csv(source, usecols=["matched_ranking"])
            .matched_ranking.dropna()
            .astype(int)
            .unique()
        )
        ranks = ranks[(ranks >= 1) & (ranks <= population_size)]
        labels[ranks - 1, issue_idx] = 1

    weights = (1 << np.arange(len(ISSUES), dtype=np.uint8))[None, :]
    masks = np.sum(labels * weights, axis=1, dtype=np.uint8)
    return np.bincount(masks, minlength=1 << len(ISSUES)).astype(np.int64)


def load_joint_counts_csv(path: Path) -> np.ndarray:
    """Read a complete mask/count table and validate its eight joint states."""
    frame = pd.read_csv(path)
    required = {"mask", "domains"}
    if not required.issubset(frame.columns):
        raise ValueError(f"{path} must contain columns {sorted(required)}")
    frame = frame.sort_values("mask")
    expected_masks = np.arange(1 << len(ISSUES))
    if not np.array_equal(frame["mask"].to_numpy(), expected_masks):
        raise ValueError(f"{path} must contain each mask from 0 through 7 exactly once")
    counts = frame["domains"].to_numpy(dtype=np.int64)
    if np.any(counts < 0) or counts.sum() == 0:
        raise ValueError("joint-state counts must be non-negative and non-empty")
    return counts


def issue_truth_from_joint_counts(joint_counts: np.ndarray) -> np.ndarray:
    """Return full-population prevalence for each bit-encoded issue."""
    bits = _mask_bits(len(joint_counts), len(ISSUES))
    return (joint_counts @ bits) / joint_counts.sum()


def simulate_nested_counts(
    joint_counts: np.ndarray,
    stages: np.ndarray,
    trials: int,
    seed: int,
) -> np.ndarray:
    """Simulate exact nested SRSWOR trajectories from joint-state counts.

    Drawing joint-state counts with a multivariate hypergeometric distribution
    is distributionally identical to randomly permuting all domains and reading
    cumulative prefixes. It preserves correlations among the three outcomes
    without materializing a population-sized label array for every trial.
    """
    if trials < 1:
        raise ValueError("trials must be positive")
    population_size = int(joint_counts.sum())
    if stages[-1] != population_size or np.any(np.diff(stages) <= 0):
        raise ValueError("stages must increase strictly and end at population size")

    bits = _mask_bits(len(joint_counts), len(ISSUES))
    rng = np.random.default_rng(seed)
    sampled_issue_counts = np.zeros(
        (trials, len(stages), len(ISSUES)), dtype=np.int64
    )

    for trial in range(trials):
        remaining = joint_counts.copy()
        cumulative_states = np.zeros_like(joint_counts)
        previous_n = 0
        for stage_idx, stage_n in enumerate(stages):
            increment = int(stage_n - previous_n)
            draw = rng.multivariate_hypergeometric(remaining, increment)
            remaining -= draw
            cumulative_states += draw
            sampled_issue_counts[trial, stage_idx] = cumulative_states @ bits
            previous_n = int(stage_n)
    return sampled_issue_counts


def _mask_bits(number_of_masks: int, number_of_issues: int) -> np.ndarray:
    expected = 1 << number_of_issues
    if number_of_masks != expected:
        raise ValueError(f"expected {expected} joint-state counts, got {number_of_masks}")
    masks = np.arange(number_of_masks, dtype=np.int64)[:, None]
    return ((masks >> np.arange(number_of_issues)[None, :]) & 1).astype(np.int64)


def approximate_normal_half_width(
    positive_counts: np.ndarray,
    stages: np.ndarray,
    population_size: int,
    z_value: float = Z_95,
) -> np.ndarray:
    """Stagewise normal-approximation 95% half-width with FPC.

    This is used as a familiar margin-of-error diagnostic, not as a claim of
    sequentially simultaneous confidence coverage.
    """
    n = stages[None, :, None].astype(float)
    estimates = positive_counts / n
    standard_error = np.sqrt(estimates * (1.0 - estimates) / n)
    fpc = np.sqrt(np.maximum(population_size - n, 0.0) / (population_size - 1))
    return z_value * standard_error * fpc


def sampling_statistics(
    positive_counts: np.ndarray,
    stages: np.ndarray,
    population_size: int,
) -> dict[str, np.ndarray]:
    """Compute estimates, cross-stage change, and relative margin of error."""
    estimates = positive_counts / stages[None, :, None]
    half_width = approximate_normal_half_width(
        positive_counts, stages, population_size
    )
    denominator = np.maximum(estimates, 1.0 / stages[None, :, None])
    relative_margin = half_width / denominator
    relative_change = np.full_like(estimates, np.inf, dtype=float)
    relative_change[:, 1:, :] = (
        np.abs(estimates[:, 1:, :] - estimates[:, :-1, :])
        / np.maximum(estimates[:, 1:, :], 1.0 / stages[None, 1:, None])
    )
    return {
        "estimates": estimates,
        "half_width": half_width,
        "relative_margin": relative_margin,
        "relative_change": relative_change,
    }


def choose_stopping_stage(
    method: str,
    statistics: dict[str, np.ndarray],
    positive_counts: np.ndarray,
    tolerance: float,
) -> np.ndarray:
    """Choose a stopping stage without access to full-population prevalence."""
    estimates = statistics["estimates"]
    eligible = np.zeros_like(estimates, dtype=bool)
    observed_positive = positive_counts > 0

    if method == "adaptive":
        eligible[:, 1:, :] = (
            observed_positive[:, 1:, :]
            & (statistics["relative_change"][:, 1:, :] <= tolerance)
            & (statistics["relative_margin"][:, 1:, :] <= tolerance)
        )
    elif method == "change_only":
        eligible[:, 1:, :] = (
            observed_positive[:, 1:, :]
            & (statistics["relative_change"][:, 1:, :] <= tolerance)
        )
    elif method == "margin_only":
        eligible[:, 1:, :] = (
            observed_positive[:, 1:, :]
            & (statistics["relative_margin"][:, 1:, :] <= tolerance)
        )
    elif method == "fixed_2pct":
        eligible[:, 0, :] = True
    elif method == "fixed_4pct":
        eligible[:, 1, :] = True
    else:
        raise ValueError(f"unknown method: {method}")

    # The census is the predeclared maximum budget, including zero-positive cases.
    eligible[:, -1, :] = True
    return np.argmax(eligible, axis=1)


def evaluate_method(
    method: str,
    positive_counts: np.ndarray,
    stages: np.ndarray,
    truth: np.ndarray,
    population_size: int,
    tolerance: float,
) -> tuple[pd.DataFrame, dict[str, np.ndarray]]:
    """Evaluate stopped estimates after the no-ground-truth rule has run."""
    statistics = sampling_statistics(positive_counts, stages, population_size)
    stop_index = choose_stopping_stage(
        method, statistics, positive_counts, tolerance
    )
    trial_index = np.arange(positive_counts.shape[0])[:, None]
    issue_index = np.arange(positive_counts.shape[2])[None, :]
    stop_n = stages[stop_index]
    stopped_estimate = statistics["estimates"][trial_index, stop_index, issue_index]
    relative_error = np.abs(stopped_estimate - truth[None, :]) / truth[None, :]
    successful = relative_error <= tolerance

    rows = []
    for issue_idx, (issue, _, prevalence_class) in enumerate(ISSUES):
        rows.append(
            {
                "method": method,
                "issue": issue,
                "prevalence_class": prevalence_class,
                "true_rate": truth[issue_idx],
                "median_stop_n": float(np.median(stop_n[:, issue_idx])),
                "mean_stop_fraction": float(
                    np.mean(stop_n[:, issue_idx] / population_size)
                ),
                "p95_stop_n": float(np.percentile(stop_n[:, issue_idx], 95)),
                "success_rate": float(np.mean(successful[:, issue_idx])),
                "median_relative_error": float(
                    np.median(relative_error[:, issue_idx])
                ),
                "p95_relative_error": float(
                    np.percentile(relative_error[:, issue_idx], 95)
                ),
                "maximum_relative_error": float(
                    np.max(relative_error[:, issue_idx])
                ),
                "full_budget_rate": float(
                    np.mean(stop_n[:, issue_idx] == population_size)
                ),
            }
        )

    details = dict(statistics)
    details.update(
        {
            "stop_index": stop_index,
            "stop_n": stop_n,
            "stopped_estimate": stopped_estimate,
            "relative_error": relative_error,
        }
    )
    return pd.DataFrame(rows), details


def representative_trajectory(
    details: dict[str, np.ndarray],
    positive_counts: np.ndarray,
    stages: np.ndarray,
    truth: np.ndarray,
    population_size: int,
) -> pd.DataFrame:
    """Return a trial whose vector of stopping points is closest to the medians."""
    median_stop = np.median(details["stop_n"], axis=0)
    distance = np.sum(
        np.abs(np.log(details["stop_n"] / median_stop[None, :])), axis=1
    )
    trial = int(np.argmin(distance))
    rows = []
    for issue_idx, (issue, _, _) in enumerate(ISSUES):
        stop_idx = int(details["stop_index"][trial, issue_idx])
        for stage_idx in range(stop_idx + 1):
            rows.append(
                {
                    "trial": trial,
                    "issue": issue,
                    "stage_n": int(stages[stage_idx]),
                    "stage_fraction": stages[stage_idx] / population_size,
                    "positive_count": int(
                        positive_counts[trial, stage_idx, issue_idx]
                    ),
                    "estimate": details["estimates"][trial, stage_idx, issue_idx],
                    "half_width": details["half_width"][trial, stage_idx, issue_idx],
                    "relative_change": details["relative_change"][
                        trial, stage_idx, issue_idx
                    ],
                    "relative_margin": details["relative_margin"][
                        trial, stage_idx, issue_idx
                    ],
                    "is_stop": stage_idx == stop_idx,
                    "full_data_rate_evaluation_only": truth[issue_idx],
                }
            )
    return pd.DataFrame(rows)


def stopping_distribution(
    stop_n: np.ndarray,
    stages: np.ndarray,
    population_size: int,
) -> pd.DataFrame:
    """Tabulate the complete per-outcome stopping-stage distribution."""
    rows = []
    trials = stop_n.shape[0]
    for issue_idx, (issue, _, prevalence_class) in enumerate(ISSUES):
        cumulative = 0
        for stage_n in stages:
            count = int(np.sum(stop_n[:, issue_idx] == stage_n))
            cumulative += count
            rows.append(
                {
                    "issue": issue,
                    "prevalence_class": prevalence_class,
                    "stage_n": int(stage_n),
                    "stage_fraction": stage_n / population_size,
                    "trial_count": count,
                    "trial_fraction": count / trials,
                    "cumulative_trial_fraction": cumulative / trials,
                }
            )
    return pd.DataFrame(rows)
