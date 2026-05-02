import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import logging
import json
import argparse
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

COLOR_RATIO_BAND = "#D8BFD8"
COLOR_RATIO_LINE = "#8B008B"
COLOR_GT_LINE = "#4682B4"
FS_LABEL = 28
FS_TICK = 24
FS_TEXT = 22
FS_LEGEND = 20

def _smooth(y, window=5):
    return pd.Series(y).rolling(window=window, min_periods=1, center=True).mean().values

def main():
    parser = argparse.ArgumentParser(description="Plot prevalence ratio between Tranco and Common Crawl (Artifact Version).")
    parser.add_argument('--cc-csv', type=str, default="data/overall_abs_sampling.csv")
    parser.add_argument('--tranco-csv', type=str, default="data/tranco_abs_sampling.csv")
    parser.add_argument('--metadata', type=str, default="data/metadata.json")
    parser.add_argument('--smooth', action='store_true')
    args = parser.parse_args()

    with open(args.metadata, 'r') as f:
        meta = json.load(f)
    tranco_baseline = meta["tranco_baseline"]
    cc_baseline = meta["cc_baseline"]
    gt_ratio = tranco_baseline / cc_baseline
    
    cc_df = pd.read_csv(args.cc_csv)
    tranco_df = pd.read_csv(args.tranco_csv)
    
    # P = Baseline + Error/100
    tranco_p_med = tranco_baseline + (tranco_df["Mean Error(%)"].values / 100.0)
    tranco_p_lo = tranco_baseline + (tranco_df["CI Lower(%)"].values / 100.0)
    tranco_p_hi = tranco_baseline + (tranco_df["CI Upper(%)"].values / 100.0)
    
    cc_p_med = cc_baseline + (cc_df["Mean Error(%)"].values / 100.0)
    cc_p_lo = cc_baseline + (cc_df["CI Lower(%)"].values / 100.0)
    cc_p_hi = cc_baseline + (cc_df["CI Upper(%)"].values / 100.0)

    ratio_med = tranco_p_med / cc_p_med
    ratio_lo = tranco_p_lo / cc_p_hi
    ratio_hi = tranco_p_hi / cc_p_lo

    if args.smooth:
        ratio_med, ratio_lo, ratio_hi = _smooth(ratio_med), _smooth(ratio_lo), _smooth(ratio_hi)

    fig, ax = plt.subplots(figsize=(14, 8))
    x_axis = cc_df['Size'].values
    ax.fill_between(x_axis, ratio_lo, ratio_hi, color=COLOR_RATIO_BAND, alpha=0.4, label="Ratio Fluctuations")
    ax.plot(x_axis, ratio_med, color=COLOR_RATIO_LINE, lw=4, label="Estimated Ratio (Tranco / CC)")
    ax.axhline(gt_ratio, color=COLOR_GT_LINE, linestyle="--", lw=3, label=f"Ground Truth Ratio ({gt_ratio:.2f}x)")

    ax.set_xlabel("Sample size", fontsize=FS_LABEL)
    ax.set_ylabel("Prevalence ratio (Tranco / CC)", fontsize=FS_LABEL)
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, pos: f'{int(x):,}'))
    ax.set_xlim(1000, 100000)
    ax.tick_params(axis='both', labelsize=FS_TICK)
    ax.grid(True, linestyle="--", alpha=0.5)
    ax.legend(fontsize=FS_LEGEND, loc="lower right", frameon=True)

    plt.tight_layout()
    plt.savefig("prevalence_ratio_tranco_cc.pdf", bbox_inches="tight")
    logger.info("Plot saved to prevalence_ratio_tranco_cc.pdf")

if __name__ == "__main__":
    main()
