"""make_charts.py — generate report figures into docs/img/.

Deterministic (no RNG). Figures:
  1. docs/img/impact_effort.png — 2x2 prioritization of the 13 opportunities.

Run: python scripts/make_charts.py
"""

from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

IMG_DIR = Path(__file__).resolve().parents[1] / "docs" / "img"

# (label, business_impact_1to5, effort S/M/L -> 1/2/3, bucket, selected?)
OPPORTUNITIES = [
    ("Discovery Copilot\n(lead scoping)", 5, 2, "Internal", True),
    ("Revio review\nintelligence", 5, 2, "Product", False),
    ("SEO / content\nengine", 4, 2, "Internal", False),
    ("Studio resume-\nto-role match", 4, 2, "Product", False),
    ("Proposal & case-study\ngenerator", 4, 2, "Internal", False),
    ("TenantEase ticket\ntriage", 4, 2, "Product", False),
    ("AI readiness audit\n(lead magnet)", 4, 1, "New product", False),
    ("AI voice intake\nagent", 4, 3, "New product", False),
    ("Internal delivery\nKB assistant", 3, 2, "Internal", False),
    ("BitElevate path\nrecommender", 3, 2, "Product", False),
    ("Delivery-risk\nearly warning", 4, 3, "Internal", False),
    ("Client onboarding\nsummarizer", 3, 2, "Customer exp.", False),
    ("Newsletter growth\nengine", 3, 2, "Internal", False),
]

BUCKET_COLORS = {
    "Internal": "#2563eb",
    "Customer exp.": "#7c3aed",
    "Product": "#db2777",
    "New product": "#059669",
}


def impact_effort_chart() -> None:
    fig, ax = plt.subplots(figsize=(9.5, 6.4), constrained_layout=True)
    for label, impact, effort, bucket, selected in OPPORTUNITIES:
        color = BUCKET_COLORS[bucket]
        if selected:
            ax.scatter(
                effort, impact, s=430, marker="*", color="#f59e0b",
                edgecolors="#78350f", linewidths=1.2, zorder=5,
            )
            ax.annotate(
                label, (effort, impact), textcoords="offset points",
                xytext=(14, 8), fontsize=8.6, fontweight="bold", color="#78350f",
            )
        else:
            ax.scatter(effort, impact, s=120, color=color, alpha=0.85, zorder=4)
            ax.annotate(
                label, (effort, impact), textcoords="offset points",
                xytext=(9, 5), fontsize=7.8, color="#374151",
            )
    # quadrant guides at midpoints
    ax.axvline(2.0, color="#9ca3af", lw=1, ls="--", zorder=1)
    ax.axhline(3.75, color="#9ca3af", lw=1, ls="--", zorder=1)
    ax.text(1.06, 4.88, "DO FIRST\n(high impact / low effort)", fontsize=8.5,
            color="#065f46", fontweight="bold", va="top")
    ax.text(2.62, 4.88, "PLAN\n(high impact / high effort)", fontsize=8.5,
            color="#7c2d12", fontweight="bold", va="top", ha="right")
    ax.text(1.06, 2.62, "FILL-INS\n(low impact / low effort)", fontsize=8.5,
            color="#374151", va="bottom")
    ax.text(2.62, 2.62, "AVOID FOR NOW", fontsize=8.5, color="#374151",
            va="bottom", ha="right")
    ax.set_xlim(0.6, 3.4)
    ax.set_ylim(2.4, 5.35)
    ax.set_xticks([1, 2, 3])
    ax.set_xticklabels(["S (<1 wk)", "M (1–3 wk)", "L (>3 wk)"])
    ax.set_yticks([3, 4, 5])
    ax.set_xlabel("POC effort (dev-weeks, single builder)")
    ax.set_ylabel("Business impact (1–5, weighted-matrix impact score)")
    ax.set_title("Cynbit AI opportunity landscape — impact vs. effort\n"
                 "(13 opportunities, weighted-matrix impact axis; star = selected POC)", fontsize=11)
    handles = [plt.Line2D([0], [0], marker="o", color="none", markerfacecolor=c,
                          markersize=9, label=b)
               for b, c in BUCKET_COLORS.items()]
    handles.append(plt.Line2D([0], [0], marker="*", color="none",
                              markerfacecolor="#f59e0b", markersize=14, label="selected"))
    ax.legend(handles=handles, loc="lower left", fontsize=8.5, framealpha=0.9,
              bbox_to_anchor=(0.0, -0.02))
    ax.grid(True, alpha=0.25, zorder=0)
    IMG_DIR.mkdir(parents=True, exist_ok=True)
    out = IMG_DIR / "impact_effort.png"
    fig.savefig(out, dpi=170)
    plt.close(fig)
    print(f"saved {out}")


if __name__ == "__main__":
    impact_effort_chart()
