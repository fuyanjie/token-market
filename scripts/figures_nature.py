#!/usr/bin/env python3
"""Nature-spec figures for the Cross-Border SIGKDD D&B v1.0 paper.

House style (傅老师's figure spec, binding for all paper figures):
  * width 89 mm (single column) or 183 mm (double column); height <= 170 mm
  * Arial/Helvetica; here Liberation Sans (metric-compatible with Arial) when
    Arial is not installed. Body text 6-7 pt, nothing below 5 pt after the
    LaTeX scale (sigconf column = 84.7 mm, so 89 mm figures shrink ~0.95x;
    we therefore use >= 6 pt everywhere). Panel labels: 8 pt bold lowercase,
    top-left.
  * lines 0.5-1 pt, axes 0.5 pt, no top/right spines, no grid, no titles
  * Okabe-Ito palette, <= 5 colours per figure, fixed colour per method
  * every estimate carries 95% CI bars / bands (paired bootstrap, B=10,000)
  * frameless legends, direct labels preferred
  * vector PDF (Type 42 fonts) + 600 dpi PNG

Reads only official result files; no numbers are computed here except
selecting rows. Re-run:  python3 scripts/figures_nature.py
"""
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import font_manager  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results", "v1.0")
OUT = os.path.join(ROOT, "docs", "latex-sigkdd-v1.0", "figures")

# ------------------------------------------------------------------ style
MM = 1 / 25.4
W1, W2 = 89 * MM, 183 * MM


def _font():
    names = {f.name for f in font_manager.fontManager.ttflist}
    for n in ("Arial", "Helvetica", "Liberation Sans", "Arimo"):
        if n in names:
            return n
    raise RuntimeError("no Arial-compatible font installed")


FONT = _font()
FS_BODY, FS_SMALL, FS_PANEL = 7, 6, 8
plt.rcParams.update({
    "font.family": "sans-serif", "font.sans-serif": [FONT],
    "mathtext.fontset": "custom", "mathtext.rm": FONT, "mathtext.it": FONT + ":italic",
    "mathtext.bf": FONT + ":bold",
    "font.size": FS_BODY, "axes.labelsize": FS_BODY,
    "xtick.labelsize": FS_SMALL, "ytick.labelsize": FS_SMALL, "legend.fontsize": FS_SMALL,
    "axes.linewidth": 0.5, "xtick.major.width": 0.5, "ytick.major.width": 0.5,
    "xtick.minor.width": 0.5, "ytick.minor.width": 0.5,
    "xtick.major.size": 2.5, "ytick.major.size": 2.5, "xtick.minor.size": 1.5, "ytick.minor.size": 1.5,
    "axes.spines.top": False, "axes.spines.right": False, "axes.grid": False,
    "lines.linewidth": 1.0, "lines.markersize": 3, "errorbar.capsize": 1.2,
    "legend.frameon": False, "pdf.fonttype": 42, "ps.fonttype": 42,
    "savefig.dpi": 600, "axes.unicode_minus": False,
})

# Okabe-Ito
OI = {"black": "#000000", "orange": "#E69F00", "skyblue": "#56B4E9", "green": "#009E73",
      "yellow": "#F0E442", "blue": "#0072B2", "vermillion": "#D55E00", "purple": "#CC79A7"}
GREY = "#999999"

# Fixed method -> style mapping, used in every figure of the paper.
# All audit arms share bluish green (statistically inseparable per Review) and
# differ by line style / marker. D3-ref is dashed everywhere.
STYLE = {
    "pilot":               dict(label="PILOT",            color=OI["vermillion"], ls="-",  marker="o"),
    "stageroute":          dict(label="StageRoute",       color=OI["blue"],       ls="-",  marker="o"),
    "strongest_fixed":     dict(label="strongest",        color=OI["orange"],     ls="-",  marker="o"),
    "cheapest_fixed":      dict(label="cheapest",         color=OI["black"],      ls="-",  marker="o"),
    "fixed_audit_a0.10":   dict(label="D3-ref (a=0.10)",  color=OI["green"],      ls=(0, (4, 1.5)),  marker="D"),
    "fixed_audit_a0.05":   dict(label="audit a=0.05",     color=OI["green"],      ls=(0, (1, 1)),    marker="v"),
    "fixed_audit_a0.20":   dict(label="audit a=0.20",     color=OI["green"],      ls=(0, (4, 1, 1, 1)), marker="^"),
    "random_audit":        dict(label="random-intensity", color=OI["green"],      ls="-",            marker="s"),
    "risk_adaptive_audit": dict(label="risk-adaptive",    color=OI["green"],      ls=(0, (6, 1, 1, 1, 1, 1)), marker="P"),
}
AUDITS = ["fixed_audit_a0.10", "fixed_audit_a0.05", "fixed_audit_a0.20", "random_audit", "risk_adaptive_audit"]
# v0.1-scale policy names -> same mapping
V01 = {"pilot_compliant": "pilot", "stageroute_compliant": "stageroute",
       "audited_compliance_cascade": "fixed_audit_a0.10"}


def panel_label(ax, s, x=-0.02, y=1.0):
    """8-pt bold lowercase, top-left of the panel (figure-relative offset)."""
    ax.annotate(s, xy=(0, 1), xycoords="axes fraction", xytext=(-14 + 0 * x, 2 + 0 * y),
                textcoords="offset points", fontsize=FS_PANEL, fontweight="bold", va="bottom", ha="left")


def save(fig, stem):
    fig.savefig(os.path.join(OUT, stem + ".pdf"))
    png = os.path.join(OUT, stem + ".png")
    fig.savefig(png, dpi=600, facecolor="white")
    from PIL import Image  # flatten to RGB (no alpha), keep 600 dpi tag
    Image.open(png).convert("RGB").save(png, dpi=(600, 600))
    plt.close(fig)
    print("wrote", stem + ".{pdf,png}")


def spread(ys, gap):
    """Return label y positions (same order) with at least `gap` between neighbours."""
    order = sorted(range(len(ys)), key=lambda i: ys[i])
    pos = [ys[i] for i in order]
    for k in range(1, len(pos)):
        pos[k] = max(pos[k], pos[k - 1] + gap)
    # re-centre the block so labels stay close to their data
    shift = (sum(pos) - sum(ys[i] for i in order)) / len(pos)
    pos = [p - shift for p in pos]
    for k in range(1, len(pos)):
        pos[k] = max(pos[k], pos[k - 1] + gap)
    out = [0] * len(ys)
    for k, i in enumerate(order):
        out[i] = pos[k]
    return out


def direct_labels(ax, items, x, gap, xpad=4):
    """items: list of (y, text, color). Labels just right of x, de-overlapped (min `gap`, data units)."""
    ys = spread([it[0] for it in items], gap)
    for (_, txt, col), y in zip(items, ys):
        ax.annotate(txt, xy=(x, y), xycoords="data", xytext=(xpad, 0), textcoords="offset points",
                    fontsize=FS_SMALL, color=col, va="center", ha="left", annotation_clip=False)


def pi_axis(ax):
    ax.set_xscale("symlog", linthresh=0.08, linscale=1.0)
    ax.set_xlim(-0.004, 1.0)
    ax.set_xticks([0, 0.05, 0.1, 0.2, 0.3, 0.5, 1.0])
    ax.set_xticklabels(["0", "0.05", "0.1", "0.2", "0.3", "0.5", "1"])
    ax.xaxis.set_minor_locator(matplotlib.ticker.NullLocator())
    ax.set_xlabel("Label reveal probability, π")


# ------------------------------------------------------------------ data
def load_main(sub="main"):
    d = json.load(open(os.path.join(RES, sub, "inference.json")))
    assert d["bootstrap"]["B"] == 10000 and d["bootstrap"]["ci"] == 0.95
    cv = {(r["pi"], r["method"]): r for r in d["curves"]}
    return d, cv


# ------------------------------------------------------------------ figures

def q_marker_fill(r, color):
    """Solid if well identifiable; half-filled if just over the 50% line
    (audit arms: 12-13/20); hollow if not identifiable."""
    if not r["identifiable"]:
        return "white", "full"
    frac = (r.get("tail_trade_rate") or {}).get("mean")
    if frac is not None and frac <= 0.65 + 1e-12:  # 13/20
        return color, "left"
    return color, "full"


def curves(ax, d, cv, key, hollow_q=False):
    pis = sorted(d["pi_grid"])
    order = AUDITS + ["cheapest_fixed", "strongest_fixed", "stageroute", "pilot"]
    for m in order:
        st = STYLE[m]
        ys = [cv[(p, m)][key]["mean"] for p in pis]
        lo = [cv[(p, m)][key]["lo"] for p in pis]
        hi = [cv[(p, m)][key]["hi"] for p in pis]
        aud = m in AUDITS
        ax.fill_between(pis, lo, hi, color=st["color"], alpha=0.10 if aud else 0.22, lw=0)
        ax.plot(pis, ys, color=st["color"], ls=st["ls"], lw=0.6 if aud else 0.9)
        if key == "Q":
            for p in pis:
                r = cv[(p, m)]
                mfc, fs = q_marker_fill(r, st["color"])
                ax.plot([p], [r["Q"]["mean"]], "o", ms=2.6, mfc=mfc, mec=st["color"],
                        mew=0.6, fillstyle=fs, zorder=5)
    return pis


def label_curves(ax, d, cv, key, gap, at=1.0):
    items = []
    for m in ["pilot", "stageroute", "strongest_fixed", "cheapest_fixed"]:
        items.append((cv[(at, m)][key]["mean"], STYLE[m]["label"], STYLE[m]["color"]))
    au = [cv[(at, m)][key]["mean"] for m in AUDITS]
    items.append((sum(au) / len(au), "audit arms (5)", OI["green"]))
    direct_labels(ax, items, at, gap)


def audit_legend(ax, loc, bbox=None, ncol=1):
    hs = [Line2D([], [], color=OI["green"], ls=STYLE[m]["ls"], lw=0.8) for m in AUDITS]
    ax.legend(hs, [STYLE[m]["label"] for m in AUDITS], loc=loc, bbox_to_anchor=bbox, ncol=ncol,
              handlelength=2.6, handletextpad=0.5, labelspacing=0.25, columnspacing=1.0,
              borderaxespad=0.2, fontsize=FS_SMALL)


def fig3(d, cv):
    fig, axs = plt.subplots(1, 2, figsize=(W2, 50 * MM))
    fig.subplots_adjust(left=0.06, right=0.885, bottom=0.195, top=0.92, wspace=0.42)
    a, b = axs
    curves(a, d, cv, "E")
    pi_axis(a); a.set_ylabel("Buyer exposure, E"); a.set_ylim(-0.01, 0.5)
    label_curves(a, d, cv, "E", gap=0.036)
    curves(b, d, cv, "Q")
    pi_axis(b); b.set_ylabel("Seller attack intent, Q"); b.set_ylim(0.45, 1.06)
    label_curves(b, d, cv, "Q", gap=0.033)
    audit_legend(a, "upper left", (0.28, 0.87), ncol=2)
    key = [
        Line2D([], [], color="k", marker="o", ls="none", ms=2.8, mfc="k", mec="k", mew=0.6, fillstyle="full"),
        Line2D([], [], color="k", marker="o", ls="none", ms=2.8, mfc="k", mec="k", mew=0.6, fillstyle="left"),
        Line2D([], [], color="k", marker="o", ls="none", ms=2.8, mfc="white", mec="k", mew=0.6, fillstyle="full"),
    ]
    b.legend(key, ["17–20/20 tail-trade runs", "just identifiable (12–13/20)", "Q not identifiable"],
             loc="upper left", bbox_to_anchor=(0.0, 1.03), ncol=3, columnspacing=0.9, handletextpad=0.3,
             borderaxespad=0.15, fontsize=FS_SMALL)
    panel_label(a, "a"); panel_label(b, "b")
    save(fig, "fig3_40seller_E_Q_vs_pi")


def figC(d, cv):
    fig, ax = plt.subplots(figsize=(W1, 55 * MM))
    fig.subplots_adjust(left=0.13, right=0.76, bottom=0.19, top=0.95)
    curves(ax, d, cv, "E_tok")
    pi_axis(ax); ax.set_ylabel("Token-weighted exposure, E$_{tok}$"); ax.set_ylim(-0.01, 0.55)
    label_curves(ax, d, cv, "E_tok", gap=0.035)
    audit_legend(ax, "upper left", (0.33, 0.89), ncol=2)
    save(fig, "figC_40seller_Etok_vs_pi")


def eq_point(ax, r, m, ms=3.2, mkr=None):
    st = STYLE[m]
    e, q = r["E"], r["Q"]
    mfc, fs = q_marker_fill(r, st["color"])
    ax.errorbar(e["mean"], q["mean"], xerr=[[e["mean"] - e["lo"]], [e["hi"] - e["mean"]]],
                yerr=[[q["mean"] - q["lo"]], [q["hi"] - q["mean"]]], fmt=mkr or st["marker"],
                color=st["color"], ms=ms, mfc=mfc, mec=st["color"], fillstyle=fs,
                mew=0.6, elinewidth=0.6, capthick=0.6, zorder=4)


def fig2(d, cv):
    """(E, Q) at pi=1 (a) and pi=0.1 (b). Single column. No front is highlighted."""
    fig, axs = plt.subplots(1, 2, figsize=(W1, 42 * MM))
    fig.subplots_adjust(left=0.115, right=0.975, bottom=0.225, top=0.91, wspace=0.40)
    for ax, pi, lab in zip(axs, (1.0, 0.1), "ab"):
        for m in AUDITS:
            eq_point(ax, cv[(pi, m)], m, ms=2.2)
        for m in ["cheapest_fixed", "strongest_fixed", "pilot", "stageroute"]:
            eq_point(ax, cv[(pi, m)], m, mkr="o")
        ax.set_xlim(-0.02, 0.5); ax.set_ylim(0.45, 1.0)
        ax.set_xticks([0, 0.1, 0.2, 0.3, 0.4, 0.5])
        ax.set_xticklabels(["0", "0.1", "0.2", "0.3", "0.4", "0.5"])
        ax.set_xlabel("Buyer exposure, E"); ax.set_ylabel("Seller attack intent, Q")
        ax.annotate(f"π = {pi:g}", xy=(0.98, 0.98), xycoords="axes fraction", ha="right",
                    va="top", fontsize=FS_SMALL)
        for m, dx, dy, ha, va in (("pilot", 0, 6, "center", "bottom"),
                                  ("stageroute", 3, 0, "left", "center"),
                                  ("strongest_fixed", 0, 6, "center", "bottom")):
            r = cv[(pi, m)]
            x0 = r["E"]["hi"] if ha == "left" else r["E"]["mean"]
            ax.annotate(STYLE[m]["label"], xy=(x0, r["Q"]["mean"]), xytext=(dx, dy),
                        textcoords="offset points", ha=ha, va=va, fontsize=FS_SMALL, color=STYLE[m]["color"])
        au = [cv[(pi, m)]["Q"]["mean"] for m in AUDITS]
        e_au = max(cv[(pi, m)]["E"]["hi"] for m in AUDITS)
        ax.annotate("audit arms (5)", xy=(e_au, sum(au) / len(au)), xytext=(6, 2), textcoords="offset points",
                    ha="left", va="bottom", fontsize=FS_SMALL, color=OI["green"])
        r = cv[(pi, "cheapest_fixed")]
        ax.annotate("cheapest", xy=(0.0, r["Q"]["mean"]), xytext=(9, -3), textcoords="offset points",
                    ha="left", va="center", fontsize=FS_SMALL, color=OI["black"])
        panel_label(ax, lab)
    save(fig, "fig2_40seller_pareto_EQ")


# ------------------------------------------------------------------ v0.1-scale (appendix)
def load_v01():
    d = json.load(open(os.path.join(RES, "T2_v01scale_20seed.json")))
    assert d["bootstrap"]["B"] == 10000
    cv = {}
    for r in d["curves"]:
        rr = dict(r)
        rr["E"] = r["fraud_share"]
        rr["identifiable"] = r["tail_trade_frac"] > 0.5
        cv[(r["pi"], V01[r["policy"]])] = rr
    return d, cv


def fig2_v01(d, cv):
    fig, axs = plt.subplots(1, 2, figsize=(W1, 46 * MM))
    fig.subplots_adjust(left=0.12, right=0.97, bottom=0.21, top=0.92, wspace=0.42)
    for ax, pi, lab in zip(axs, (1.0, 0.1), "ab"):
        for m in ["fixed_audit_a0.10", "stageroute", "pilot"]:
            eq_point(ax, cv[(pi, m)], m, mkr="o" if m != "fixed_audit_a0.10" else "D")
        ax.set_xlim(-0.005, 0.14); ax.set_ylim(0.0, 1.0)
        ax.set_xticks([0, 0.05, 0.1]); ax.set_xticklabels(["0", "0.05", "0.1"])
        ax.set_xlabel("Buyer exposure, E"); ax.set_ylabel("Seller attack intent, Q")
        ax.annotate(f"π = {pi:g}", xy=(0.97, 0.5), xycoords="axes fraction", ha="right", fontsize=FS_SMALL)
        sr = (6, 0, "left") if pi == 1.0 else (0, -15, "center")
        for m, dx, dy, ha in (("pilot", 0, 7, "center"), ("stageroute",) + sr,
                              ("fixed_audit_a0.10", 0, 9, "center")):
            r = cv[(pi, m)]
            ax.annotate(STYLE[m]["label"] if m != "fixed_audit_a0.10" else "D3-ref",
                        xy=(r["E"]["mean"], r["Q"]["mean"]), xytext=(dx, dy),
                        textcoords="offset points", ha=ha, va="center", fontsize=FS_SMALL,
                        color=STYLE[m]["color"])
        panel_label(ax, lab)
    save(fig, "fig2_v01scale_pareto_EQ")


def fig3_v01(d, cv):
    pis = sorted(d["pi_grid"])
    fig, axs = plt.subplots(1, 2, figsize=(W2, 55 * MM))
    fig.subplots_adjust(left=0.06, right=0.9, bottom=0.18, top=0.93, wspace=0.38)
    for ax, key, ylab, lab in zip(axs, ("E", "Q"), ("Buyer exposure, E", "Seller attack intent, Q"), "ab"):
        items = []
        for m in ["fixed_audit_a0.10", "stageroute", "pilot"]:
            st = STYLE[m]
            ys = [cv[(p, m)][key]["mean"] for p in pis]
            ax.fill_between(pis, [cv[(p, m)][key]["lo"] for p in pis], [cv[(p, m)][key]["hi"] for p in pis],
                            color=st["color"], alpha=0.2, lw=0)
            ax.plot(pis, ys, color=st["color"], ls=st["ls"], lw=0.9)
            if key == "Q":
                for p in pis:
                    r = cv[(p, m)]
                    if not r["identifiable"]:
                        ax.plot([p], [r["Q"]["mean"]], "o", ms=2.6, mew=0.6, mec=st["color"],
                                mfc="white", zorder=5)
            items.append((cv[(1.0, m)][key]["mean"], "D3-ref" if m == "fixed_audit_a0.10" else st["label"],
                          st["color"]))
        ax.set_xscale("symlog", linthresh=0.05)
        ax.set_xlim(-0.003, 1.0)
        ax.set_xticks([0, 0.05, 0.1, 0.2, 1.0]); ax.set_xticklabels(["0", "0.05", "0.1", "0.2", "1"])
        ax.xaxis.set_minor_locator(matplotlib.ticker.NullLocator())
        ax.set_xlabel("Label reveal probability, π"); ax.set_ylabel(ylab)
        ax.set_ylim(0, 0.72 if key == "E" else 1.0)
        direct_labels(ax, items, 1.0, 0.045 if key == "E" else 0.06)
        panel_label(ax, lab)
    axs[1].annotate("hollow: Q not identifiable", xy=(0.02, 0.45), xycoords="axes fraction",
                    fontsize=FS_SMALL, va="center", ha="left")
    save(fig, "fig3_v01scale_E_Q_vs_pi")


if __name__ == "__main__":
    print("font:", FONT)
    d, cv = load_main("main")
    fig2(d, cv)
    fig3(d, cv)
    figC(d, cv)
    dv, cvv = load_v01()
    fig2_v01(dv, cvv)
    fig3_v01(dv, cvv)
