#!/usr/bin/env python3
"""Interactive assistant for the adaptive probability sampling strategy.

Implements the stopping rule from the paper (Section 8, Practical Guidance):

  - declare a frame of size N and a relative tolerance tau;
  - draw a 2% pilot; the pilot cannot stop (no previous estimate to compare);
  - at every later stage, stop only when x_k > 0 AND
        D_k = |p_k - p_{k-1}| / p_k <= tau   (relative change)
        R_k = h_k / p_k <= tau               (relative CI half-width)
    where h_k is the half-width of an approximate 95% proportion interval
    with finite-population correction;
  - otherwise double the cumulative sample, with N as the predeclared max.

The researcher only enters the observed number of affected units x_k at each
stage; the assistant reports the estimate, the two stopping statistics, the
decision, and the next sample size.

Usage:
    python3 adaptive_sampling_assistant.py
    python3 adaptive_sampling_assistant.py --frame-size 500000 --tau 0.05
    python3 adaptive_sampling_assistant.py --frame-size 100000 --tau 0.05 \
        --stages 2000,4000,8000,16000,32000,64000,100000
    python3 adaptive_sampling_assistant.py --frame-size 100000 --tau 0.05 \
        --batch 4000,934 8000,1867 16000,3734

Only the Python standard library is required.
"""

from __future__ import annotations

import argparse
import math
import sys
from dataclasses import dataclass


def normal_quantile(p: float) -> float:
    """Standard normal quantile Phi^{-1}(p) via binary search on math.erf.

    math.erf is in the standard library, so no third-party dependency is
    needed; 60 bisection iterations give full double-precision accuracy.
    """
    from math import erf, sqrt

    def cdf(z: float) -> float:
        return 0.5 * (1.0 + erf(z / sqrt(2.0)))

    lo, hi = -9.0, 9.0
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        if cdf(mid) < p:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def z_for_confidence(level_percent: float) -> float:
    """Two-sided normal quantile for a confidence level in percent."""
    if level_percent <= 0 or level_percent >= 100:
        raise ValueError("confidence level must be in (0, 100)")
    alpha = 1.0 - level_percent / 100.0
    return normal_quantile(1.0 - alpha / 2.0)


def default_stages(population_size: int, pilot_fraction: float = 0.02) -> list[int]:
    """2% pilot, then doubling until the frame is covered."""
    stages = [max(1, round(population_size * pilot_fraction))]
    while stages[-1] < population_size:
        stages.append(min(2 * stages[-1], population_size))
    return stages


def ci_half_width(p_hat: float, n: int, n_total: int, z: float) -> float:
    """Approximate 95% proportion half-width with finite-population correction."""
    if n <= 0 or n_total <= 1:
        return 0.0
    se = math.sqrt(max(p_hat * (1.0 - p_hat), 0.0) / n)
    fpc = math.sqrt(max(n_total - n, 0) / (n_total - 1))
    return z * se * fpc


@dataclass
class StageResult:
    stage_index: int
    n: int
    x: int
    p_hat: float
    relative_change: float | None   # None for the pilot stage
    relative_half_width: float | None
    can_stop: bool
    reasons: list[str]
    next_n: int | None


def evaluate_stage(
    *,
    stage_index: int,
    n: int,
    x: int,
    n_total: int,
    tau: float,
    z: float,
    previous_p: float | None,
) -> StageResult:
    reasons: list[str] = []
    p_hat = x / n if n > 0 else 0.0

    if x == 0:
        reasons.append("no positive cases observed (x=0)")

    if stage_index == 1:
        reasons.append("pilot stage: no previous estimate for comparison")

    relative_change: float | None = None
    relative_half_width: float | None = None

    if previous_p is not None and p_hat > 0:
        relative_change = abs(p_hat - previous_p) / p_hat
        if relative_change > tau:
            reasons.append(f"relative change {relative_change:.4f} > tau {tau:.3f}")
    elif previous_p is not None:
        relative_change = float("inf")

    if p_hat > 0 and x > 0:
        h = ci_half_width(p_hat, n, n_total, z)
        relative_half_width = h / p_hat
        if relative_half_width > tau:
            reasons.append(
                f"relative CI half-width {relative_half_width:.4f} > tau {tau:.3f}"
            )

    can_stop = not reasons and relative_change is not None and relative_half_width is not None
    next_n = min(2 * n, n_total) if n < n_total else None
    if next_n is not None and next_n == n:
        next_n = None

    return StageResult(
        stage_index=stage_index,
        n=n,
        x=x,
        p_hat=p_hat,
        relative_change=relative_change,
        relative_half_width=relative_half_width,
        can_stop=can_stop,
        reasons=reasons,
        next_n=next_n,
    )


def run_interactive(
    n_total: int,
    tau: float,
    confidence: float,
    stages: list[int],
) -> None:
    z = z_for_confidence(confidence)
    print()
    print("=" * 66)
    print("Adaptive Probability Sampling Assistant")
    print("=" * 66)
    print(f"Frame size N        : {n_total:,}")
    print(f"Relative tolerance τ: {tau:.3f}")
    print(f"Confidence level    : {confidence:.0f}%  (z = {z:.3f})")
    print(f"Stages (cumulative) : {', '.join(f'{s:,}' for s in stages)}")
    print("Enter the number of affected units observed at each stage.")
    print("Type 'q' to quit.")
    print("-" * 66)

    previous_p: float | None = None
    for idx, n in enumerate(stages, start=1):
        if idx > 1 and n == stages[idx - 2]:
            continue
        while True:
            prompt = f"Stage {idx} (n={n:,}): affected units x = "
            raw = input(prompt).strip()
            if raw.lower() in ("q", "quit", "exit"):
                print("Aborted.")
                return
            try:
                x = int(raw)
            except ValueError:
                print("  Please enter an integer.")
                continue
            if x < 0 or x > n:
                print(f"  x must be between 0 and {n:,}.")
                continue
            break

        res = evaluate_stage(
            stage_index=idx,
            n=n,
            x=x,
            n_total=n_total,
            tau=tau,
            z=z,
            previous_p=previous_p,
        )
        pct = res.p_hat * 100.0
        print(f"  Estimate p = {res.p_hat:.6f} ({pct:.3f}%)")
        if res.relative_change is not None:
            print(f"  Relative change D = {res.relative_change:.4f}")
        else:
            print("  Relative change D = n/a (pilot)")
        if res.relative_half_width is not None:
            print(f"  Relative CI half-width R = {res.relative_half_width:.4f}")
        else:
            print("  Relative CI half-width R = n/a")

        if res.can_stop:
            print("  >>> STOP: both conditions satisfied. Report the estimate.")
            print("      Confidence interval half-width (absolute): "
                  f"{ci_half_width(res.p_hat, n, n_total, z):.6f}")
            return
        if res.next_n is None:
            print("  >>> Reached the complete frame; report the full-frame rate.")
            return
        for reason in res.reasons:
            print(f"  - continue: {reason}")
        print(f"  >>> CONTINUE: collect {res.next_n - n:,} additional units "
              f"(cumulative {res.next_n:,}).")
        previous_p = res.p_hat

    print("No stage satisfied the stopping conditions; the complete frame "
          "was measured as the predeclared fallback.")


def run_batch(
    n_total: int,
    tau: float,
    confidence: float,
    observations: list[tuple[int, int]],
) -> None:
    """Non-interactive evaluation of an explicit sequence of (n, x) pairs."""
    z = z_for_confidence(confidence)
    previous_p: float | None = None
    print(f"N={n_total:,}  tau={tau:.3f}  confidence={confidence:.0f}%")
    print("-" * 66)
    for idx, (n, x) in enumerate(observations, start=1):
        res = evaluate_stage(
            stage_index=idx,
            n=n,
            x=x,
            n_total=n_total,
            tau=tau,
            z=z,
            previous_p=previous_p,
        )
        pct = res.p_hat * 100.0
        status = "STOP" if res.can_stop else "CONTINUE"
        print(
            f"stage {idx}: n={n:>9,} x={x:>9,} p={pct:8.3f}%  "
            f"D={res.relative_change if res.relative_change is None else round(res.relative_change,4)}  "
            f"R={res.relative_half_width if res.relative_half_width is None else round(res.relative_half_width,4)}  "
            f"=> {status}"
        )
        if res.can_stop:
            return
        previous_p = res.p_hat
    print("Reached the end of the observation sequence without stopping.")


def parse_batch(values: list[str]) -> list[tuple[int, int]]:
    obs = []
    for item in values:
        parts = item.split(",")
        if len(parts) != 2:
            raise argparse.ArgumentTypeError(f"expected n,x got {item!r}")
        obs.append((int(parts[0]), int(parts[1])))
    return obs


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Interactive adaptive probability sampling assistant."
    )
    parser.add_argument("--frame-size", type=int, default=500_000,
                        help="declared population size N")
    parser.add_argument("--tau", type=float, default=0.05,
                        help="relative tolerance for both stopping conditions")
    parser.add_argument("--confidence", type=float, default=95.0,
                        help="confidence level in percent (default 95)")
    parser.add_argument("--pilot-fraction", type=float, default=0.02,
                        help="pilot fraction of N (default 0.02)")
    parser.add_argument("--stages", type=str, default=None,
                        help="comma-separated cumulative sample sizes "
                             "(default: 2% pilot then doubling)")
    parser.add_argument("--batch", nargs="+", type=str, default=None,
                        metavar="n,x",
                        help="non-interactive: evaluate (n,x) pairs, e.g. "
                             "--batch 4000,934 8000,1867")
    args = parser.parse_args()

    if args.frame_size <= 0:
        parser.error("--frame-size must be positive")
    if not 0 < args.tau < 1:
        parser.error("--tau must be in (0, 1)")
    if not 0 < args.pilot_fraction < 1:
        parser.error("--pilot-fraction must be in (0, 1)")

    if args.stages:
        stages = [int(s) for s in args.stages.split(",")]
        if stages[-1] != args.frame_size:
            print(f"note: last stage {stages[-1]:,} != N {args.frame_size:,}; "
                  "the frame will be used as the final fallback.",
                  file=sys.stderr)
            stages.append(args.frame_size)
    else:
        stages = default_stages(args.frame_size, args.pilot_fraction)

    if args.batch:
        obs = parse_batch(args.batch)
        run_batch(args.frame_size, args.tau, args.confidence, obs)
    else:
        run_interactive(args.frame_size, args.tau, args.confidence, stages)


if __name__ == "__main__":
    main()
