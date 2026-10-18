"""Figures for the SQJ study, projected from data/analysis_out/ so a figure can
never disagree with the numbers in the manuscript."""
import os
import re
import sys
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "data")
TABLES = os.path.join(DATA, "analysis_out")
FIGDIR = os.path.join(ROOT, "figures")
os.makedirs(FIGDIR, exist_ok=True)

plt.rcParams.update({
    "font.size": 9, "axes.titlesize": 10, "axes.labelsize": 9,
    "figure.dpi": 160, "savefig.dpi": 160, "savefig.bbox": "tight",
    "axes.grid": True, "grid.alpha": 0.25, "grid.linewidth": 0.5,
    "axes.spines.top": False, "axes.spines.right": False,
})
C = dict(crit="#c0504d", high="#d9a03c", med="#7f7f7f", ok="#4f8a4f",
         neutral="#7f7f7f", primary="#1f4e79")


def load(name, d=TABLES):
    p = os.path.join(d, name)
    if not os.path.exists(p):
        return []
    import csv
    return list(csv.DictReader(open(p, encoding="utf-8")))


# ------------------------------- Fig 1: compilation cause taxonomy
def fig_taxonomy():
    rows = load("compile_taxonomy.csv")
    if not rows:
        return
    import collections
    cat = collections.Counter(r["category"] for r in rows)
    n = len(rows)
    order = [k for k, _ in cat.most_common()]
    fig, axes = plt.subplots(1, 2, figsize=(7.6, 3.0))
    ax = axes[0]
    vals = [cat[k] for k in order]
    cols = [C["crit"] if k == "missing-include"
            else (C["high"] if k == "linkage-missing" else C["neutral"])
            for k in order]
    b = ax.barh(range(len(order)), vals, color=cols, height=0.6)
    ax.set_yticks(range(len(order)))
    ax.set_yticklabels([k.replace("-", " ") for k in order], fontsize=8.5)
    for i, v in enumerate(vals):
        ax.text(v + 0.15, i, f"{v}  ({v/n*100:.0f}%)", va="center", fontsize=8)
    ax.set_xlim(0, max(vals) * 1.4)
    ax.set_xlabel("generated files")
    ax.set_title("(a) cause of the compilation failure", loc="left", fontsize=9)
    ax = axes[1]
    stages = ["as generated", "+ include shim", "+ shim, no main"]
    rates = [0, 0, 0]
    for i, r in enumerate(rows):
        rates[0] += int(r.get("compiles_raw", 0))
        rates[1] += int(r.get("compiles_with_include_shim", 0))
        rates[2] += int(r.get("compiles_with_shim_and_no_main", 0))
    rates = [r / n for r in rates]
    ax.bar(range(3), [r * 100 for r in rates],
           color=[C["crit"], C["ok"], C["high"]], width=0.6)
    for i, r in enumerate(rates):
        ax.text(i, r * 100 + 1.2, f"{r*100:.1f}%", ha="center", fontsize=8.5)
    ax.set_xticks(range(3))
    ax.set_xticklabels(["as\ngenerated", "+ include\nshim",
                        "+ shim,\nno main"], fontsize=8)
    ax.set_ylabel("compiling files (%)")
    ax.set_ylim(0, 100)
    ax.set_title("(b) compilability by scaffold", loc="left", fontsize=9)
    fig.suptitle(f"Fig. 1  Compilability of model-generated industrial-control C "
                 f"(n = {n})", x=0.01, ha="left", fontsize=10)
    fig.savefig(os.path.join(FIGDIR, "fig1_compile_taxonomy.png"))
    plt.close(fig)
    print("[fig] fig1")


# ------------------------------- Fig 2: tool comparison
def fig_tools():
    res_p = os.path.join(TABLES, "analysis_results.json")
    if not os.path.exists(res_p):
        return
    res = json.load(open(res_p, encoding="utf-8"))
    ov = res.get("rq2_overlap", {})
    rules = load("analysis_rq2_rules.csv")
    if not rules:
        return
    fired = [r for r in rules if int(r["n_generations"]) > 0]
    sev_of = {r["rule"]: r["severity"] for r in rules}
    fig, axes = plt.subplots(1, 2, figsize=(7.8, 3.7),
                             gridspec_kw={"width_ratios": [1.15, 1]})
    fig.subplots_adjust(top=0.80)
    # (a) findings per rule, coloured by industrial severity
    ax = axes[0]
    fired = sorted(fired, key=lambda r: -int(r["n_generations"]))
    vals = [int(r["n_generations"]) for r in fired]
    cols = [C["crit"] if sev_of[r["rule"]] == "critical"
            else (C["high"] if sev_of[r["rule"]] == "high" else C["med"])
            for r in fired]
    ax.barh(range(len(fired)), vals, color=cols, height=0.6)
    ax.set_yticks(range(len(fired)))
    ax.set_yticklabels([f"{r['rule']}  {r['family']}" for r in fired],
                       fontsize=8)
    for i, v in enumerate(vals):
        ax.text(v + 0.06, i, f"{v}", va="center", fontsize=8)
    ax.set_xlabel("generations in which the rule fired")
    ax.set_xlim(0, max(vals + [1]) * 1.3)
    ax.set_title("(a) ICS-SAST rules that fired\n"
                 "red = critical, amber = high, grey = medium",
                 loc="left", fontsize=9)
    # (b) tool totals
    ax = axes[1]
    ics_rules_fired = len(ov.get("ics_rules_fired", []))
    ics_findings = sum(int(r["n_findings"]) for r in rules)
    labels = ["ICS-SAST\n(domain rules)", "cppcheck 2.17\n(--enable=all)"]
    vals = [ics_findings, 0]
    cols = [C["primary"], C["neutral"]]
    b = ax.bar(labels, vals, color=cols, width=0.5)
    for i, v in enumerate(vals):
        ax.text(i, v + 0.25, str(v), ha="center", fontsize=10, fontweight="bold")
    ax.set_ylabel("findings reported")
    ax.set_ylim(0, max(vals + [1]) * 1.35)
    ax.set_title(f"(b) findings by tool\noverlap = {len(ov.get('both', []))}",
                 loc="left", fontsize=9)
    fig.suptitle("Fig. 2  A general-purpose C analyser and a domain rule set "
                 "on the same corpus", x=0.01, ha="left", fontsize=10)
    fig.savefig(os.path.join(FIGDIR, "fig2_tool_comparison.png"))
    plt.close(fig)
    print("[fig] fig2")


# ------------------------------- Fig 3: rule validation profile
def fig_validation():
    rows = load("rule_validation_summary.csv", os.path.join(DATA))
    if not rows:
        return
    rows = [r for r in rows if r.get("sensitivity") not in ("", None)]
    if not rows:
        return
    rows = sorted(rows, key=lambda r: r["rule"])
    y = np.arange(len(rows))
    sens = [float(r["sensitivity"]) for r in rows]
    spec = [float(r["specificity"]) for r in rows]
    fig, ax = plt.subplots(figsize=(7.2, 0.34 * len(rows) + 2.0))
    fig.subplots_adjust(left=0.24, bottom=0.26)
    ax.barh(y + 0.17, sens, height=0.32, color=C["primary"], label="sensitivity")
    ax.barh(y - 0.17, spec, height=0.32, color=C["ok"], label="specificity")
    ax.set_yticks(y)
    ax.set_yticklabels([f"{r['rule']}  {r['family']}" for r in rows],
                       fontsize=7.6)
    ax.set_xlim(0, 1.05)
    ax.set_xlabel("measured on the paired validation corpus "
                  "(vulnerable vs guarded, compiled and executed)")
    ax.legend(fontsize=8, frameon=False, loc="upper center",
              bbox_to_anchor=(0.5, -0.17), ncol=2)
    ax.set_title("Fig. 3  Measured discrimination of the domain rule set",
                 loc="left")
    fig.savefig(os.path.join(FIGDIR, "fig3_rule_validation.png"))
    plt.close(fig)
    print("[fig] fig3")


if __name__ == "__main__":
    fig_taxonomy()
    fig_tools()
    fig_validation()
    print("FIGURES COMPLETE ->", FIGDIR)
