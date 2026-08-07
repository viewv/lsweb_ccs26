# Adaptive Probability Sampling — Case Study (CCS 2026 B #4135 revision artifact)

This directory contains the code and minimal frozen results for the adaptive
probability sampling case study reported in Section 8 (Practical Guidance for
Sampling) and the corresponding appendix of the revised paper.

## Frozen configuration (5%)

```
pilot:               2%
later stages:        4%, 8%, 16%, 32%, 64%, 100%
sampling:            nested simple random sampling without replacement
relative change:     <= 0.05
relative CI margin:  <= 0.05
trials:              1,000 retrospective random permutations
seed:                20260722
outcomes:            Cookie security, Clickjacking, CORS
```

The 2% pilot cannot stop. Starting at 4%, a run stops only when at least one
positive case has been observed and both the cross-stage relative change and
the relative half-width of the stagewise approximate 95% interval (with
finite-population correction) are at most 5%. The 100% stage is the
predeclared fallback. The stopping rule never receives the full-frame rate;
the full-frame rate is used only after stopping to evaluate relative error.

## Directory layout

```
adaptive_case_study/
├── README.md
├── requirements.txt
├── run_all_5pct.sh                 # end-to-end reproduction (tests + 3 experiments)
├── adaptive_sampling.py            # core algorithm (nested SRSWOR, stopping rule)
├── run_experiment.py               # shared experiment driver
├── run_tranco_experiment.py        # Tranco Top-500K
├── run_tranco_top100k_impact_experiment.py  # Tranco Top-100K
├── run_commoncrawl_experiment.py   # Common Crawl processed hosts
├── test_adaptive_sampling.py       # 8 unit tests
├── plot_results.py                 # figure generation (optional)
└── results_5pct/                   # frozen minimal results
    ├── SHA256SUMS
    ├── tranco/                     # adaptive_results.csv, stopping_distribution.csv, metadata.json
    ├── tranco_top100k_impact/
    └── commoncrawl/
```

## Self-contained reproduction

This directory is self-contained: the frozen eight-state joint counts for all
three frames are bundled under `data/` (they encode the per-domain/per-host
outcome labels used in the paper, including the Common Crawl 24,834,442-host
frame). No external data access is needed.

```
data/
├── tranco_joint_counts.csv            # Tranco Top-500K
├── tranco_top100k_joint_counts.csv    # Tranco Top-100K
└── commoncrawl_joint_counts.csv       # Common Crawl processed hosts
```

The original `data/` inputs were reconstructed from the paper's issue-level
lists (Tranco `impact/cat_issues` cookie/click/acao CSVs; Common Crawl
`domain_issue_wide` table). The run scripts read the bundled joint counts by
default and accept `--joint-counts` to point elsewhere.

## Reproduction

Requirements: Python 3.10+, numpy, pandas, matplotlib.

```bash
python3 -m pip install -r requirements.txt
./run_all_5pct.sh        # unit tests + all three experiments
```

The script writes results to `results_repro/` and figures to `figures_repro/`
by default, so re-running never overwrites the frozen `results_5pct/`. To run
a quick sanity check: `TRIALS=5 ./run_all_5pct.sh`. Frozen outputs are the
authoritative numbers reported in the paper.

## Correspondence to the paper table

| Frame | Outcome | Median stop | Mean stop | Max stop | Accuracy |
|---|---|---|---|---|---|
| Tranco Top-100K | Cookie security | 8% | 8.14% | 16% | 99.0% |
| Tranco Top-100K | Clickjacking | 16% | 16.37% | 32% | 98.3% |
| Tranco Top-100K | CORS | 100% | 100.00% | 100% | 100.0% |
| Tranco Top-500K | Cookie security | 4% | 4.00% | 4% | 99.9% |
| Tranco Top-500K | Clickjacking | 4% | 4.10% | 8% | 99.2% |
| Tranco Top-500K | CORS | 64% | 65.01% | 100% | 99.9% |
| Common Crawl | Cookie security | 4% | 4.00% | 4% | 100.0% |
| Common Crawl | Clickjacking | 4% | 4.00% | 4% | 100.0% |
| Common Crawl | CORS | 4% | 4.02% | 8% | 99.0% |

Median/mean/max stopping fractions come from
`adaptive_results.csv` and `stopping_distribution.csv`; accuracy is the
fraction of trials whose stopped estimate is within 5% relative error of the
full-frame rate (`success_rate` in `adaptive_results.csv`).

## Integrity

`results_5pct/SHA256SUMS` protects every frozen result file. The frozen 5%
experiment was independently rerun and verified byte-for-byte on 2026-07-24.
