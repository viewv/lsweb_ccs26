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

def print_peak_rms_line(id, ax, stats, color_peak, color_rms, x_pos=0.03, y_offset=0.05):
    py_peak = stats["peak_original"]
    py_rms = stats["rms"]
    ax.axhline(py_peak, color=color_peak, linestyle="--", lw=1.5, alpha=0.8)
    ax.axhline(py_rms, color=color_rms, linestyle="-.", lw=1.5, alpha=0.8)

    trans_peak = blended_transform_factory(ax.transAxes, ax.transData)
    offset_up = transforms.ScaledTranslation(0, y_offset, ax.figure.dpi_scale_trans)
    peak_val = Decimal(str(abs(stats['peak_original']))).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    rms_val = Decimal(str(round(stats["rms"], 3))).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    ax.text(x_pos, py_peak, f"{id} |Peak|={peak_val}", fontsize=FS_TEXT, color=color_peak,
            ha="left", va="bottom", transform=trans_peak + offset_up)
    ax.text(x_pos + 0.18, py_rms, f"{id} RMS={rms_val}", fontsize=FS_TEXT, color=color_rms,
            ha="left", va="bottom", transform=trans_peak + offset_up)

def main():
    parser = argparse.ArgumentParser(description="Plot prevalence deviation against own baselines (Artifact Version).")
    parser.add_argument("--cc-csv", type=str, default="data/overall_abs_sampling.csv")
    parser.add_argument("--tranco-csv", type=str, default="data/tranco_abs_sampling.csv")
    parser.add_argument("--smooth", action="store_true", help="Apply smoothing to curves")
    args = parser.parse_args()
    
    plt.rcParams.update({
        'font.size': FS_TICK, 'axes.labelsize': FS_LABEL, 'xtick.labelsize': FS_TICK,
        'ytick.labelsize': FS_TICK, 'legend.fontsize': FS_LEGEND,
        'pdf.fonttype': 42, 'ps.fonttype': 42
    })
    
    cc_df = pd.read_csv(args.cc_csv)
    tranco_df = pd.read_csv(args.tranco_csv)
    
    x_axis = cc_df['Size'].values
    tranco_med, tranco_lo, tranco_hi = tranco_df['Mean Error(%)'].values, tranco_df['CI Lower(%)'].values, tranco_df['CI Upper(%)'].values
    cc_med, cc_lo, cc_hi = cc_df['Mean Error(%)'].values, cc_df['CI Lower(%)'].values, cc_df['CI Upper(%)'].values
    
    if args.smooth:
        def _smooth(y, window=5):
            return pd.Series(y).rolling(window=window, min_periods=1, center=True).mean().values
        tranco_med, tranco_lo, tranco_hi = _smooth(tranco_med), _smooth(tranco_lo), _smooth(tranco_hi)
        cc_med, cc_lo, cc_hi = _smooth(cc_med), _smooth(cc_lo), _smooth(cc_hi)

    fig, ax = plt.subplots(figsize=(14, 9))
    fig.subplots_adjust(left=0.12)
    
    COLOR_RND_BAND = "#A6CEE3"
    COLOR_RND_MED = "#1F78B4"
    COLOR_SVR_BAND = "#B2DF8A"
    COLOR_SVR_MED = "#33A02C"
    
    ax.fill_between(x_axis, tranco_lo, tranco_hi, color=COLOR_RND_BAND, alpha=0.30, label="Random Tranco (50% interval)")
    ax.plot(x_axis, tranco_med, color=COLOR_RND_MED, lw=2.6)
    ax.fill_between(x_axis, cc_lo, cc_hi, color=COLOR_SVR_BAND, alpha=0.40, label="Random Common (50% interval)")
    ax.plot(x_axis, cc_med, color=COLOR_SVR_MED, lw=2.5)

    ax.axhline(0, color="gray", linestyle="--", lw=1.0, alpha=0.8)
    ax.grid(True, linestyle="--", alpha=0.55)
    ax.set_yscale("symlog", linthresh=0.1, linscale=0.5, base=10)
    
    abs_peak = max(np.max(np.abs(cc_df['Peak Signed(%)'].values)), np.max(np.abs(tranco_df['Peak Signed(%)'].values)))
    YMAX = max(10.0, float(np.ceil(abs_peak * 1.5 / 5.0) * 5.0))
    ax.set_ylim(-YMAX, YMAX)
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.1f"))

    tranco_stats = {"peak_original": tranco_df["Peak Signed(%)"].values[np.argmax(np.abs(tranco_df["Peak Signed(%)"].values))], "rms": np.sqrt(np.mean(tranco_df["RMS(%)"]**2))}
    cc_stats = {"peak_original": cc_df["Peak Signed(%)"].values[np.argmax(np.abs(cc_df["Peak Signed(%)"].values))], "rms": np.sqrt(np.mean(cc_df["RMS(%)"]**2))}
    
    print_peak_rms_line("Tranco", ax, tranco_stats, color_peak="#005CB8", color_rms="#4682B4", x_pos=0.05, y_offset=-0.40)
    print_peak_rms_line("Common", ax, cc_stats, color_peak="#008000", color_rms="#2E8B57", x_pos=0.03, y_offset=0.25)

    ax.set_xlim(1000, 100000)
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, pos: f'{int(x):,}'))
    ax.set_xlabel("Sample size", fontsize=FS_LABEL)
    ax.set_ylabel("Deviation from baseline (%)", fontsize=FS_LABEL)
    ax.legend(frameon=True, loc="upper right")
    
    plt.tight_layout()
    plt.savefig("prevalence_deviation_own_baseline.pdf", bbox_inches="tight")
    logger.info("Plot saved to prevalence_deviation_own_baseline.pdf")

if __name__ == "__main__":
    main()
