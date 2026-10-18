"""Statistics for the SQJ study, computed from the tables scan_corpus.py wrote.

Kept separate from the scanning stage so a failure in an external analyser
cannot take the reporting down, and so the numbers can be regenerated without
re-running cppcheck.
"""
import os
import sys
import csv
import json
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "data")
TABLES = os.path.join(DATA, "analysis_out")
sys.path.insert(0, os.path.join(ROOT, "..", "00_shared"))
sys.path.insert(0, HERE)
import stats_core as ST  # noqa: E402
import ics_rules as R  # noqa: E402

VALID_SUMMARY = os.path.join(DATA, "rule_validation_summary.csv")
REFERENCE = os.path.join(DATA, "reference_solution.c")


def load(name, d=TABLES):
    p = os.path.join(d, name)
    return list(csv.DictReader(open(p, encoding="utf-8"))) \
        if os.path.exists(p) else []


def num(v, cast=float):
    try:
        return cast(v)
    except (TypeError, ValueError):
        return None


def prep(s):
    s = re.sub(r"/\*.*?\*/", " ", s, flags=re.S) if False else s
    return s


import re  # noqa: E402  (used by prep above)


def main():
    per = load("per_generation.csv")
    if not per:
        print("no per_generation.csv -- run scan_corpus.py first")
        return
    for r in per:
        for k in ("compiles_raw", "compiles_with_include_shim",
                  "ics_findings", "ics_findings_no_main", "ics_critical",
                  "ics_high", "ics_medium", "cppcheck_findings", "lines",
                  "n_functions", "has_main", "uses_float", "uses_malloc",
                  "severity_critical_task", "cppcheck_error",
                  "cppcheck_warning", "cppcheck_style", "cppcheck_portability",
                  "compiles_with_shim_and_no_main"):
            r[k] = num(r.get(k), int) or 0
        r["lines"] = num(r.get("lines"), int) or 0

    tax_p = os.path.join(TABLES, "compile_taxonomy.json")
    tax = json.load(open(tax_p, encoding="utf-8")) if os.path.exists(tax_p) \
        else {}

    out = {
        "population": dict(
            n_generations=len(per),
            n_models=len({r["model"] for r in per}),
            n_tasks=len({r["task"] for r in per}),
            n_functions_total=sum(r["n_functions"] for r in per),
            median_lines=ST.quantile(sorted(r["lines"] for r in per), .5),
        ),
        "rq1_compilability": tax or "run compile_taxonomy.py first",
    }

    # ---- RQ1: compilability and its causes
    r1 = []
    if tax:
        r1 = [dict(stage="as generated",
                   n_compiling=tax["compiles_raw"],
                   rate=round(tax["compiles_raw"] / tax["n"], 4)),
              dict(stage="with include shim",
                   n_compiling=tax["compiles_with_shim"],
                   rate=round(tax["compiles_with_shim"] / tax["n"], 4)),
              dict(stage="with shim and no user main",
                   n_compiling=tax["compiles_with_shim_no_main"],
                   rate=round(tax["compiles_with_shim_no_main"] / tax["n"], 4))]
        ST.write_csv(r1, os.path.join(TABLES, "analysis_rq1_compilability.csv"))
    out["rq1_table"] = r1
    if tax:
        print(f"[rq1] raw {tax['compiles_raw']}/{tax['n']}, "
              f"with shim {tax['compiles_with_shim']}/{tax['n']}")
        print(f"[rq1] causes {tax['categories_raw']}")

    # ---- RQ2: anti-pattern rates vs the human reference
    ref_rules = set()
    ref_n = 0
    if os.path.exists(REFERENCE):
        import ics_rules as RR
        s = open(REFERENCE, encoding="utf-8").read()
        s = re.sub(r"/\*.*?\*/", " ", s, flags=re.S)
        s = re.sub(r"//[^\n]*", " ", s)
        s = re.sub(r'"(\\.|[^"\\])*"', '""', s)
        d = {}
        for m in re.finditer(r"^\s*#\s*define\s+([A-Za-z_]\w*)\s+(.+?)\s*$",
                             s, re.M):
            d[m.group(1)] = m.group(2).strip()
        h, _ = RR.analyze(s, d)
        ref_rules = {x["rule_id"] for x in h}
        ref_n = len(h)
    gen_gens = len(per)
    # true per-rule finding counts: raw tool-output rows in findings.csv
    # (the per-generation 'ics_rules' column is a de-duplicated rule SET)
    find_by_rule = {}
    _fpath = os.path.join(TABLES, "findings.csv")
    if os.path.exists(_fpath):
        for _row in csv.DictReader(open(_fpath, encoding="utf-8")):
            _rid = _row.get("rule_id") or ""
            find_by_rule[_rid] = find_by_rule.get(_rid, 0) + 1
    r2 = []
    for r in R.RULES:
        rid = r["id"]
        n_gens = sum(1 for x in per if rid in (x.get("ics_rules") or "").split(";"))
        r2.append(dict(rule=rid, family=r["family"], cwe=r["cwe"],
                       severity=r["severity"],
                       n_generations=n_gens,
                       gen_rate=round(n_gens / gen_gens, 4) if gen_gens else 0,
                       n_findings=find_by_rule.get(rid, 0),
                       in_human_reference=int(rid in ref_rules),
                       description=r["description"]))
    r2.sort(key=lambda x: -x["n_generations"])
    ST.write_csv(r2, os.path.join(TABLES, "analysis_rq2_rules.csv"))
    out["rq2_rules"] = r2
    out["rq2_reference"] = dict(n_findings=ref_n, rules=sorted(ref_rules))
    print(f"[rq2] human reference findings={ref_n} rules={sorted(ref_rules)}")

    # detection overlap between the two tools
    ics_ids = set()
    for x in per:
        ics_ids.update(y for y in (x.get("ics_rules") or "").split(";") if y)
    cpp_ids = set()
    for x in per:
        cpp_ids.update(y.split(":")[0] for y in
                       (x.get("cppcheck_ids") or "").split(";") if y)
    out["rq2_overlap"] = dict(
        ics_rules_fired=sorted(ics_ids),
        cppcheck_ids_fired=sorted(cpp_ids),
        both=sorted(ics_ids & cpp_ids),
        ics_only=sorted(ics_ids - cpp_ids),
        cppcheck_only=sorted(cpp_ids - ics_ids))
    print(f"[rq2] ics fired {sorted(ics_ids)}; cppcheck {sorted(cpp_ids)}")

    # ---- RQ3: what predicts findings
    crit = [x["ics_findings"] for x in per if x["severity_critical_task"]]
    non = [x["ics_findings"] for x in per if not x["severity_critical_task"]]
    r3 = dict(
        critical_task=ST.describe(crit, "critical"),
        noncritical_task=ST.describe(non, "non-critical"),
        spearman_lines_vs_findings=ST.spearman(
            [x["lines"] for x in per], [x["ics_findings"] for x in per]),
        spearman_functions_vs_findings=ST.spearman(
            [x["n_functions"] for x in per], [x["ics_findings"] for x in per]),
    )
    if len(crit) >= 3 and len(non) >= 3:
        t = ST.mannwhitney_u(crit, non)
        t["cliffs_delta"] = ST.cliffs_delta(crit, non)
        r3["test_critical_vs_noncritical"] = t
        print(f"[rq3] critical vs non-critical p={t.get('p')}")
    per_task = defaultdict(list)
    for x in per:
        per_task[x["task"]].append(x["ics_findings"])
    r3["per_task"] = [dict(task=k, n=len(v),
                           mean_findings=round(sum(v) / len(v), 3),
                           median=ST.quantile(sorted(v), .5),
                           subsystem=next((x["subsystem"] for x in per
                                           if x["task"] == k), ""))
                      for k, v in sorted(per_task.items(),
                                         key=lambda x: -sum(x[1]) / len(x[1]))]
    out["rq3"] = r3

    # ---- severity profile
    out["severity_profile"] = dict(
        critical=sum(x["ics_critical"] for x in per),
        high=sum(x["ics_high"] for x in per),
        medium=sum(x["ics_medium"] for x in per),
        cppcheck_error=sum(x["cppcheck_error"] for x in per),
        cppcheck_warning=sum(x["cppcheck_warning"] for x in per),
        cppcheck_style=sum(x["cppcheck_style"] for x in per),
        cppcheck_portability=sum(x["cppcheck_portability"] for x in per),
        generations_with_any_critical=sum(1 for x in per if x["ics_critical"]),
        uses_float=sum(x["uses_float"] for x in per),
        uses_malloc=sum(x["uses_malloc"] for x in per),
        has_user_main=sum(x["has_main"] for x in per),
    )
    print("[severity]", out["severity_profile"])

    # ---- rule-set validation, restated next to the corpus result
    if os.path.exists(VALID_SUMMARY):
        vs = load("rule_validation_summary.csv", os.path.dirname(VALID_SUMMARY))
        out["rule_validation"] = vs
        sens = [num(v["sensitivity"]) for v in vs if v.get("sensitivity")]
        spec = [num(v["specificity"]) for v in vs if v.get("specificity")]
        if sens:
            out["rule_validation_summary"] = dict(
                n_rules=len(vs),
                median_sensitivity=ST.quantile(sorted(sens), .5),
                median_specificity=ST.quantile(sorted(spec), .5)
                if spec else None,
                rules_with_sensitivity_1=sum(1 for v in sens if v == 1.0),
                rules_with_false_positives=[
                    v["rule"] for v in vs
                    if num(v["false_positives"], int)])
            print(f"[rules] median sens={out['rule_validation_summary']['median_sensitivity']} "
                  f"spec={out['rule_validation_summary']['median_specificity']}")

    p = os.path.join(TABLES, "analysis_results.json")
    json.dump(out, open(p, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    print(f"[write] {p}")
    print("STATS COMPLETE")


if __name__ == "__main__":
    main()
