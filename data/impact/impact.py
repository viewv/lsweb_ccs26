import json
import argparse
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from decimal import Decimal, ROUND_HALF_UP
from matplotlib.ticker import MaxNLocator, AutoMinorLocator
import matplotlib.transforms as transforms
from matplotlib.transforms import blended_transform_factory


def draw_fig2(data, out_pdf="./fig2.pdf"):
    """Reproduce the figure from the pre-computed data dict."""
    x_ratio = data["x_ratio"]
    top     = data["top"]
    sys_c,  sys_lo,  sys_hi = data["sys_c"],  data["sys_lo"],  data["sys_hi"]
    rnd_c,  rnd_lo,  rnd_hi = data["rnd_c"],  data["rnd_lo"],  data["rnd_hi"]
    str_c,  str_lo,  str_hi = data["str_c"],  data["str_lo"],  data["str_hi"]
    swing_stats             = data["swing_stats"]
    params                  = data["params"]
    band         = params["band"]
    band_mode    = params["band_mode"]
    error_metric = params.get("error_metric", "signed_pp")

    # ── canvas ───────────────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(17, 5))

    COLOR_TOP      = "#6b24bf"
    COLOR_SYS_BAND = "#FDB863";  COLOR_SYS_MED = "#E66101"
    COLOR_RND_BAND = "#A6CEE3";  COLOR_RND_MED = "#1F78B4"
    COLOR_STR_BAND = "#B2DF8A";  COLOR_STR_MED = "#33A02C"

    ax.plot(x_ratio, top, color=COLOR_TOP, lw=2.5, label="Top N", zorder=3)

    label_suffix = (f"mean, {int(band*100)}% interval" if band_mode == "meancenter"
                    else f"median, {int(band*100)}% interval")

    ax.fill_between(x_ratio, sys_lo, sys_hi,
                    color=COLOR_SYS_BAND, alpha=0.4,
                    label=f"Systematic ({label_suffix})")
    ax.plot(x_ratio, sys_c, color=COLOR_SYS_MED, lw=2.2)

    ax.fill_between(x_ratio, rnd_lo, rnd_hi,
                    color=COLOR_RND_BAND, alpha=0.4,
                    label=f"Random ({label_suffix})")
    ax.plot(x_ratio, rnd_c, color=COLOR_RND_MED, lw=2.2)

    if str_c:
        ax.fill_between(x_ratio, str_lo, str_hi,
                        color=COLOR_STR_BAND, alpha=0.35,
                        label=f"Stratified ({label_suffix})")
        ax.plot(x_ratio, str_c, color=COLOR_STR_MED, lw=2.2)

    ax.axhline(0, color="gray", linestyle="--", lw=1.0, alpha=0.8)

    ylabel = {
        "signed_pp":        "Deviation from baseline (%)",
        "relative_pct":     "Relative error from baseline (%)",
        "abs_relative_pct": "Absolute relative error (%)",
    }[error_metric]
    label_font_size = 18
    ax.set_xlabel("Sample size as a fraction of full website population",
                  fontsize=label_font_size)
    ax.set_ylabel(ylabel, fontsize=label_font_size)
    ax.tick_params(axis='x', labelsize=16)
    ax.tick_params(axis='y', labelsize=16)
    ax.xaxis.set_major_locator(MaxNLocator(nbins=20))
    ax.xaxis.set_minor_locator(AutoMinorLocator(4))

    lin = 0.12
    ax.set_yscale("symlog", linthresh=lin, linscale=2.5, base=10)

    def _fmt(v):
        return Decimal(str(round(v, 4))).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP
        )

    def _annotate(label, stats, COLOR_PEAK, COLOR_RMS, x_peak, x_rms):
        if stats is None:
            return
        ax.axhline(stats["peak_original"],
                   color=COLOR_PEAK, linestyle="--", lw=2, alpha=0.8)
        ax.axhline(stats["rms"],
                   color=COLOR_RMS,  linestyle="-.", lw=2, alpha=0.8)
        trans  = blended_transform_factory(ax.transAxes, ax.transData)
        offset = transforms.ScaledTranslation(0, 0.02, ax.figure.dpi_scale_trans)
        ax.text(x_peak, stats["peak_original"],
                f"{label} |Peak|={_fmt(stats['peak_abs'])}",
                fontsize=16, color=COLOR_PEAK, ha="left", va="bottom",
                transform=trans + offset)
        ax.text(x_rms,  stats["rms"],
                f"{label} RMS={_fmt(stats['rms'])}",
                fontsize=16, color=COLOR_RMS,  ha="left", va="bottom",
                transform=trans + offset)

    _annotate("Top",        swing_stats["top"],
              "#5A1E9A", "#3A3A3A", 0.02, 0.02)
    _annotate("Random",     swing_stats["random"],
              "#125EAB", "#156abf", 0.35, 0.35)
    _annotate("Systematic", swing_stats["systematic"],
              "#D97A00", "#A85E00", 0.65, 0.65)
    _annotate("Stratified", swing_stats["stratified"],
              "#1E7A32", "#145523", 0.50, 0.85)

    p_ticks = [15, 5, 1.5, 0.4, 0.12, 0.1, 0.08, 0.06, 0.04, 0.02]
    ticks   = sorted(p_ticks + [-x for x in p_ticks] + [0])
    ax.set_yticks(ticks)
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.2f"))
    ax.grid(True, which="major", linestyle="--", alpha=0.6, linewidth=0.9)
    ax.grid(True, which="minor", linestyle=":",  alpha=0.3, linewidth=0.6)
    ax.legend(frameon=True, fontsize=15, loc="best")
    ax.set_xlim(0.0, 0.5)

    plt.tight_layout()
    if out_pdf:
        fig.savefig(out_pdf, bbox_inches="tight", pad_inches=0)
        print(f"Saved → {out_pdf}")
    return fig, ax


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="./impact_overall.json",
                        help="Path to impact_overall.json (default: ./impact_overall.json)")
    parser.add_argument("--out",  default="./fig2.pdf",
                        help="Output PDF path (default: ./fig2.pdf)")
    args = parser.parse_args()

    with open(args.data) as f:
        data = json.load(f)

    params = data.get("params", {})
    print(f"  issue: All Issues | "
          f"N_POP={params.get('N_POP')} | "
          f"repeats={params.get('repeats')} | "
          f"seed={params.get('seed')}")
    print(f"  {len(data['x_ratio'])} sample-size steps loaded.")

    fig, ax = draw_fig2(data, out_pdf=args.out)
    plt.show()
