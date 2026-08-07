#!/usr/bin/env python3
"""Generate all paper figures from saved CSV/JSON experiment outputs.

This script never reruns sampling. Figure styling can therefore be changed
independently of the experiment implementation and random seed.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


HERE = Path(__file__).resolve().parent
COLORS = {
    "adaptive": "#4C78A8",
    "fixed_2pct": "#F28E2B",
    "fixed_4pct": "#ECA82C",
    "change_only": "#E15759",
    "margin_only": "#B279A2",
    "truth": "#2F4B7C",
    "stop": "#59A14F",
}
METHOD_LABELS = {
    "fixed_2pct": "Fixed 2%",
    "fixed_4pct": "Fixed 4%",
    "change_only": "Change only",
    "margin_only": "Margin only",
    "adaptive": "Adaptive",
}


def _short_issue_labels(issues):
    return ["Cookie\nsecurity" if issue == "Cookie security" else issue for issue in issues]


def _load(results_dir: Path):
    metadata = json.loads((results_dir / "metadata.json").read_text())
    comparison = pd.read_csv(results_dir / "method_comparison.csv")
    distribution = pd.read_csv(results_dir / "stopping_distribution.csv")
    trajectory = pd.read_csv(results_dir / "representative_trajectory.csv")
    return metadata, comparison, distribution, trajectory


def _save(fig, figure_dir: Path, stem: str) -> None:
    figure_dir.mkdir(parents=True, exist_ok=True)
    fig.savefig(figure_dir / f"{stem}.png", dpi=300, bbox_inches="tight")
    fig.savefig(figure_dir / f"{stem}.pdf", bbox_inches="tight")
    plt.close(fig)


def plot_method_summary(results_dir: Path, figure_dir: Path, stem: str) -> None:
    metadata, comparison, _, _ = _load(results_dir)
    adaptive = comparison[comparison.method == "adaptive"].copy()
    issues = adaptive.issue.tolist()
    population_size = int(metadata["population_size"])
    tolerance = float(metadata["relative_change_tolerance"])

    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.1))
    x = np.arange(len(issues))
    issue_labels = _short_issue_labels(issues)
    stop_fraction = adaptive.median_stop_n.to_numpy() / population_size * 100
    axes[0].bar(x, stop_fraction, color=COLORS["adaptive"], width=0.62)
    for idx, value in enumerate(stop_fraction):
        axes[0].text(idx, value + max(1.0, value * 0.035), f"{value:.0f}%", ha="center", fontsize=8)
    axes[0].set_xticks(x, issue_labels)
    axes[0].set_ylabel("Population sampled (%)")
    axes[0].set_title("Median adaptive stopping stage")
    upper_limit = 110 if stop_fraction.max() >= 95 else max(
        10, stop_fraction.max() * 1.25
    )
    axes[0].set_ylim(0, upper_limit)
    axes[0].grid(axis="y", linewidth=0.5, alpha=0.28)

    methods = ["fixed_2pct", "fixed_4pct", "change_only", "adaptive"]
    width = 0.19
    for method_idx, method in enumerate(methods):
        part = comparison[comparison.method == method].set_index("issue")
        values = np.array([part.loc[issue, "success_rate"] for issue in issues]) * 100
        offset = (method_idx - (len(methods) - 1) / 2) * width
        axes[1].bar(
            x + offset,
            values,
            width,
            color=COLORS[method],
            label=METHOD_LABELS[method],
        )
    axes[1].set_xticks(x, issue_labels)
    axes[1].set_ylabel(f"Runs within ±{tolerance:.0%} error (%)")
    axes[1].set_ylim(0, 105)
    axes[1].set_title("Retrospective reliability")
    axes[1].grid(axis="y", linewidth=0.5, alpha=0.28)
    axes[1].legend(frameon=False, fontsize=7, ncol=2, loc="lower right")

    fig.suptitle(metadata["population"], fontsize=10, y=0.995)
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    _save(fig, figure_dir, f"{stem}_method_summary")


def plot_stopping_distribution(
    results_dir: Path, figure_dir: Path, stem: str
) -> None:
    metadata, _, distribution, _ = _load(results_dir)
    issues = list(distribution.issue.drop_duplicates())
    stages = sorted(distribution.stage_fraction.unique())
    matrix = np.zeros((len(issues), len(stages)))
    for issue_idx, issue in enumerate(issues):
        part = distribution[distribution.issue == issue].set_index("stage_fraction")
        matrix[issue_idx] = [part.loc[stage, "trial_fraction"] * 100 for stage in stages]

    fig, ax = plt.subplots(figsize=(7.2, 2.3))
    image = ax.imshow(matrix, cmap="Blues", vmin=0, vmax=100, aspect="auto")
    ax.set_xticks(np.arange(len(stages)), [f"{stage:.0%}" for stage in stages])
    ax.set_yticks(np.arange(len(issues)), issues)
    ax.set_xlabel("Cumulative population sampled at stopping")
    ax.set_title(f"{metadata['population']}: stopping-stage distribution")
    for row in range(matrix.shape[0]):
        for column in range(matrix.shape[1]):
            value = matrix[row, column]
            if value > 0:
                ax.text(
                    column,
                    row,
                    f"{value:.1f}%",
                    ha="center",
                    va="center",
                    color="white" if value >= 55 else "black",
                    fontsize=8,
                )
    colorbar = fig.colorbar(image, ax=ax, pad=0.02)
    colorbar.set_label("Trials (%)")
    fig.tight_layout()
    _save(fig, figure_dir, f"{stem}_stopping_distribution")


def plot_representative_trajectory(
    results_dir: Path, figure_dir: Path, stem: str
) -> None:
    metadata, _, _, trajectory = _load(results_dir)
    is_impact = str(metadata.get("measurement_objective", "")).startswith("impact")
    rate_label = "affected-site rate" if is_impact else "prevalence"
    issues = list(trajectory.issue.drop_duplicates())
    fig, axes = plt.subplots(1, len(issues), figsize=(7.5, 2.8), squeeze=False)
    axes = axes[0]

    for ax, issue in zip(axes, issues):
        part = trajectory[trajectory.issue == issue]
        x = part.stage_fraction.to_numpy() * 100
        estimate = part.estimate.to_numpy() * 100
        half_width = part.half_width.to_numpy() * 100
        ax.errorbar(
            x,
            estimate,
            yerr=half_width,
            marker="o",
            markersize=4,
            color=COLORS["adaptive"],
            ecolor="#9ECAE1",
            capsize=2,
            linewidth=1.2,
            label="Estimate ± approximate 95% margin",
        )
        truth = float(part.full_data_rate_evaluation_only.iloc[0] * 100)
        ax.axhline(
            truth,
            color=COLORS["truth"],
            linestyle="--",
            linewidth=1.1,
            label=f"Full-frame {rate_label} (evaluation only)",
        )
        stopped = part[part.is_stop].iloc[0]
        ax.scatter(
            [stopped.stage_fraction * 100],
            [stopped.estimate * 100],
            color=COLORS["stop"],
            marker="D",
            s=25,
            zorder=4,
            label="Stopped estimate",
        )
        ax.set_title(f"{issue}\nstop at {stopped.stage_fraction:.0%}", fontsize=9)
        ax.set_xlabel("Cumulative sample (%)")
        ax.set_ylabel(f"Estimated {rate_label} (%)")
        ax.grid(linewidth=0.5, alpha=0.28)

    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(
        handles,
        labels,
        loc="lower center",
        bbox_to_anchor=(0.5, -0.01),
        ncol=3,
        frameon=False,
        fontsize=7,
    )
    fig.suptitle(metadata["population"], y=0.995, fontsize=10)
    fig.tight_layout(rect=(0, 0.13, 1, 0.93))
    _save(fig, figure_dir, f"{stem}_representative_trajectory")


def plot_cross_dataset(
    tranco_dir: Path, commoncrawl_dir: Path, figure_dir: Path
) -> None:
    tranco_meta, tranco, _, _ = _load(tranco_dir)
    common_meta, common, _, _ = _load(commoncrawl_dir)
    datasets = [
        ("Tranco", tranco_meta, tranco[tranco.method == "adaptive"]),
        ("Common Crawl", common_meta, common[common.method == "adaptive"]),
    ]
    issues = datasets[0][2].issue.tolist()
    issue_labels = _short_issue_labels(issues)
    x = np.arange(len(issues))
    width = 0.36

    fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.8))
    for dataset_idx, (label, metadata, frame) in enumerate(datasets):
        stop = frame.median_stop_n.to_numpy() / int(metadata["population_size"]) * 100
        success = frame.success_rate.to_numpy() * 100
        offset = (dataset_idx - 0.5) * width
        axes[0].bar(x + offset, stop, width, label=label)
        axes[1].bar(x + offset, success, width, label=label)

    axes[0].set_xticks(x, issue_labels)
    axes[0].set_ylabel("Median cumulative sample (%)")
    axes[0].set_title("Adaptive stopping cost")
    axes[0].grid(axis="y", linewidth=0.5, alpha=0.28)
    axes[1].set_xticks(x, issue_labels)
    axes[1].set_ylabel("Runs within target error (%)")
    axes[1].set_ylim(0, 105)
    axes[1].set_title("Stopped-estimate reliability")
    axes[1].grid(axis="y", linewidth=0.5, alpha=0.28)
    axes[1].legend(frameon=False, fontsize=8, loc="lower right")
    fig.tight_layout()
    _save(fig, figure_dir, "cross_dataset_comparison")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--tranco-results", type=Path, default=HERE / "results" / "tranco"
    )
    parser.add_argument(
        "--commoncrawl-results",
        type=Path,
        default=HERE / "results" / "commoncrawl",
    )
    parser.add_argument(
        "--tranco-top100k-impact-results",
        type=Path,
        default=HERE / "results" / "tranco_top100k_impact",
    )
    parser.add_argument("--figure-dir", type=Path, default=HERE / "figures")
    args = parser.parse_args()

    for results_dir, stem in (
        (args.tranco_results, "tranco"),
        (args.tranco_top100k_impact_results, "tranco_top100k_impact"),
        (args.commoncrawl_results, "commoncrawl"),
    ):
        plot_method_summary(results_dir, args.figure_dir, stem)
        plot_stopping_distribution(results_dir, args.figure_dir, stem)
        plot_representative_trajectory(results_dir, args.figure_dir, stem)
    plot_cross_dataset(
        args.tranco_results, args.commoncrawl_results, args.figure_dir
    )
    print(f"Figures written to {args.figure_dir}")


if __name__ == "__main__":
    main()
