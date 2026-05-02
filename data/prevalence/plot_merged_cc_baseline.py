import pandas as pd
import numpy as np
import argparse
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.transforms import blended_transform_factory
import matplotlib.transforms as transforms
from decimal import Decimal, ROUND_HALF_UP
import logging
import json
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# Font sizes for publication-ready plots
FS_LABEL = 28
FS_TICK = 24
FS_TEXT = 22
FS_LEGEND = 20

def print_peak_line(id, ax, stats, color_peak, x_pos=0.03, y_offset=0.05):
    py_peak = stats["peak_original"]
    ax.axhline(py_peak, color=color_peak, linestyle="--", lw=1.5, alpha=0.8)

    trans_peak = blended_transform_factory(ax.transAxes, ax.transData)
    offset_up = transforms.ScaledTranslation(0, y_offset, ax.figure.dpi_scale_trans)
    peak_val = Decimal(str(abs(stats['peak_original']))).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    ax.text(x_pos, py_peak, f"{id} |Peak|={peak_val}", fontsize=FS_TEXT, color=color_peak,
            ha="left", va="bottom", transform=trans_peak + offset_up)

def main():
    parser = argparse.ArgumentParser(description="Plot prevalence deviation against Common Crawl baseline (Artifact Version).")
    parser.add_argument("--cc-csv", type=str, default="data/overall_abs_sampling.csv")
    parser.add_argument("--tranco-csv", type=str, default="data/tranco_abs_sampling.csv")
    parser.add_argument("--metadata", type=str, default="data/metadata.json")
    parser.add_argument("--smooth", action="store_true", help="Apply smoothing to curves")
    args = parser.parse_args()
    
    plt.rcParams.update({
        'font.size': FS_TICK, 'axes.labelsize': FS_LABEL, 'xtick.labelsize': FS_TICK,
        'ytick.labelsize': FS_TICK, 'legend.fontsize': FS_LEGEND,
        'pdf.fonttype': 42, 'ps.fonttype': 42
    })
    
    # Load metadata
    with open(args.metadata, 'r') as f:
        meta = json.load(f)
    tranco_baseline = meta["tranco_baseline"]
    cc_baseline = meta["cc_baseline"]
    tranco_bias = (tranco_baseline - cc_baseline) * 100.0
    
    # Load pre-computed sampling data
    cc_df = pd.read_csv(args.cc_csv)
    tranco_df = pd.read_csv(args.tranco_csv)
    
    x_axis = cc_df['Size'].values
    
    # tranco_df errors are relative to its own baseline. Shift them to CC baseline.
    tranco_med = tranco_df['Mean Error(%)'].values + tranco_bias
    tranco_lo = tranco_df['CI Lower(%)'].values + tranco_bias
    tranco_hi = tranco_df['CI Upper(%)'].values + tranco_bias
    
    cc_med = cc_df['Mean Error(%)'].values
    cc_lo = cc_df['CI Lower(%)'].values
    cc_hi = cc_df['CI Upper(%)'].values

    use_broken_y = abs(tranco_bias) > 3.0
    if use_broken_y:
        fig, (ax_top, ax_bot) = plt.subplots(2, 1, sharex=True, figsize=(14, 9), gridspec_kw={'height_ratios': [1, 1]})
        fig.subplots_adjust(hspace=0.12, left=0.12)
        axes = [ax_top, ax_bot]
    else:
        fig, ax = plt.subplots(figsize=(14, 9))
        fig.subplots_adjust(left=0.12)
        axes = [ax]
        ax_top = ax_bot = ax
    
    COLOR_RND_BAND = "#A6CEE3"
    COLOR_RND_MED = "#1F78B4"
    COLOR_SVR_BAND = "#B2DF8A"
    COLOR_SVR_MED = "#33A02C"
    
    if args.smooth:
        def _smooth(y, window=5):
            return pd.Series(y).rolling(window=window, min_periods=1, center=True).mean().values
        tranco_med, tranco_lo, tranco_hi = _smooth(tranco_med), _smooth(tranco_lo), _smooth(tranco_hi)
        cc_med, cc_lo, cc_hi = _smooth(cc_med), _smooth(cc_lo), _smooth(cc_hi)

    if use_broken_y:
        if tranco_bias < 0:
            ax_common, ax_tranco = ax_top, ax_bot
        else:
            ax_common, ax_tranco = ax_bot, ax_top
            
        ax_common.fill_between(x_axis, cc_lo, cc_hi, color=COLOR_SVR_BAND, alpha=0.40, label="Random Common (50% interval)")
        ax_common.plot(x_axis, cc_med, color=COLOR_SVR_MED, lw=2.5)
        ax_common.axhline(0, color="gray", linestyle="--", lw=1.0, alpha=0.8)
        
        ax_tranco.fill_between(x_axis, tranco_lo, tranco_hi, color=COLOR_RND_BAND, alpha=0.30, label="Random Tranco (50% interval)")
        ax_tranco.plot(x_axis, tranco_med, color=COLOR_RND_MED, lw=2.6)
        ax_tranco.axhline(tranco_bias, color=COLOR_RND_MED, linestyle=":", lw=1.5, alpha=0.8)
        
        pad_common = max(2.0, np.max(np.abs(cc_df['Peak Signed(%)'].values)) * 1.3)
        ax_common.set_ylim(-pad_common, pad_common)
        
        tranco_max_dev = max(np.max(np.abs(tranco_hi - tranco_bias)), np.max(np.abs(tranco_lo - tranco_bias)))
        pad_tranco = max(0.5, tranco_max_dev * 1.3)
        ax_tranco.set_ylim(tranco_bias - pad_tranco, tranco_bias + pad_tranco)
        
        for a in axes:
            a.set_xlim(1000, 100000)
            a.grid(True, linestyle="--", alpha=0.55)
            a.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.2f"))
            
        ax_top.spines['bottom'].set_visible(False)
        ax_bot.spines['top'].set_visible(False)
        ax_top.xaxis.tick_top()
        ax_top.tick_params(labeltop=False)
        
        d = .015
        kwargs_top = dict(transform=ax_top.transAxes, color='k', clip_on=False)
        kwargs_bot = dict(transform=ax_bot.transAxes, color='k', clip_on=False)
        ax_top.plot((-d, +d), (-d, +d), **kwargs_top)
        ax_top.plot((1 - d, 1 + d), (-d, +d), **kwargs_top)
        ax_bot.plot((-d, +d), (1 - d, 1 + d), **kwargs_bot)
        ax_bot.plot((1 - d, 1 + d), (1 - d, 1 + d), **kwargs_bot)
        
        cc_stats = {"peak_original": cc_df["Peak Signed(%)"].values[np.argmax(np.abs(cc_df["Peak Signed(%)"].values))]}
        tranco_stats = {"peak_original": tranco_df["Peak Signed(%)"].values[np.argmax(np.abs(tranco_df["Peak Signed(%)"].values))] + tranco_bias}
        print_peak_line("Common", ax_common, cc_stats, color_peak="#008000", x_pos=0.10, y_offset=0.08)
        print_peak_line("Tranco", ax_tranco, tranco_stats, color_peak="#005CB8", x_pos=0.15, y_offset=-0.15)
    else:
        # Standard Plotting
        pass # Similar logic if not broken

    fig.supylabel("Deviation from baseline (%)", fontsize=FS_LABEL, x=0.04)
    ax_bot.set_xlabel("Sample size", fontsize=FS_LABEL)
    ax_top.legend(frameon=True, loc="upper right")
    
    plt.tight_layout()
    plt.savefig("prevalence_deviation_cc_baseline.pdf", bbox_inches="tight")
    logger.info("Plot saved to prevalence_deviation_cc_baseline.pdf")

if __name__ == "__main__":
    main()
