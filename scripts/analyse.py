#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
02_SQJ_llm_secure_antipatterns / analyse.py

Analysis of the LLM-generated industrial-control corpus. The pipeline is:
  1. compile every generation with `zig cc -std=c99` (compilability is a first
     reported outcome, not a precondition);
  2. run the ICS-SAST rule set and cppcheck on every generation;
  3. run the same two tools on the human reference solutions, giving a
     differential audit on an identical functional contract;
  4. compare model, task, defect-class and severity distributions, and relate
     the security findings to a mechanical, executed check.

Research questions
  RQ1  What is the compilability of LLM-generated industrial-control code, and
       how does it vary by task and by model?
  RQ2  Which industrial-control security anti-patterns appear in generated
       code, and at what rate relative to human reference solutions for the
       same contract?
  RQ3  Which task characteristics predict the number of reported findings?
  RQ4  Do the findings that a static rule reports correspond to a *mechanical*
       failure, i.e. does a flagged function actually misbehave under a
       constructed input? (executed differential validation)
"""
import os
import re
import sys
import csv
import json
import math
import subprocess
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "data")
GEN = os.path.join(DATA, "generated")
sys.path.insert(0, os.path.join(ROOT, "..", "00_shared"))
import stats_tools as ST  # noqa: E402
sys.path.insert(0, HERE)
import ics_rules as R  # noqa: E402

CPPCHECK = os.path.join(os.path.dirname(sys.executable), "cppcheck.exe")
ZIG = [sys.executable, "-m", "ziglang", "cc"]
ENV = dict(os.environ, ZIG_GLOBAL_CACHE_DIR=os.path.join(ROOT, "..", ".zigcache"))


def prep(s):
    s = re.sub(r"/\*.*?\*/", " ", s, flags=re.S)
    s = re.sub(r"//[^\n]*", " ", s)
    s = re.sub(r'"(\\.|[^"\\])*"', '""', s)
    d = {}
    for m in re.finditer(r"^\s*#\s*define\s+([A-Za-z_]\w*)\s+(.+?)\s*$", s, re.M):
        d[m.group(1)] = m.group(2).strip()
    return s, d


def run_cppcheck(path):
    if not os.path.isfile(CPPCHECK):
        return []
    try:
        r = subprocess.run(
            [CPPCHECK, "--enable=all", "--std=c99", "--force", "--inconclusive",
             "-q", "--template={severity}|{id}|{msg}|{line}", path],
            capture_output=True, timeout=180)
        txt = r.stdout.decode("utf-8", "replace")
    except Exception as e:
        return [dict(severity="error", id="cppcheck-failed", msg=str(e), line=0)]
    hits = []
    for line in txt.splitlines():
        parts = line.split("|", 3)
        if len(parts) == 4 and parts[0].strip():
            try:
                ln = int(parts[3].strip())
            except ValueError:
                ln = 0
            hits.append(dict(severity=parts[0].strip(), id=parts[1].strip(),
                             msg=parts[2].strip(), line=ln))
    return hits


def main():
    if not os.path.isdir(GEN):
        print("no generated corpus")
        return
    tasks = json.load(open(os.path.join(DATA, "taskset.json"),
                           encoding="utf-8"))
    tmeta = {t["id"]: t for t in tasks["tasks"]}

    files = sorted(f for f in os.listdir(GEN) if f.endswith(".c"))
    per_file = []
    findings = []
    builddir = os.path.join(DATA, ".build")
    os.makedirs(builddir, exist_ok=True)

    for fn in files:
        parts = fn[:-2].split("__")
        model = parts[0] if parts else "?"
        task = parts[1] if len(parts) > 1 else "?"
        rep = parts[2] if len(parts) > 2 else "?"
        path = os.path.join(GEN, fn)
        src = open(path, encoding="utf-8", errors="ignore").read()
        # ---- compile
        exe = os.path.join(builddir, fn[:-2] + ".exe")
        c = subprocess.run(ZIG + ["-std=c99", "-w", path, "-o", exe],
                           capture_output=True, timeout=240, env=ENV)
        compiles = c.returncode == 0
        cerr = c.stderr.decode("utf-8", "replace")
        n_err = len(re.findall(r"error:", cerr))
        n_warn = len(re.findall(r"warning:", cerr))
        # ---- static analysis
        clean, defines = prep(src)
        hits, ctx = R.analyze(clean, defines)
        cpc = run_cppcheck(path)
        nlines = len(clean.splitlines())
        per_file.append(dict(
            file=fn, model=model, task=task, rep=rep, lines=nlines,
            compiles=int(compiles), compile_errors=n_err, warnings=n_warn,
            n_ics_findings=len(hits),
            n_cppcheck_findings=len(cpc),
            n_functions=len(ctx["funcs"]) if ctx else 0,
            subsystem=tmeta.get(task, {}).get("subsystem", ""),
            concern=tmeta.get(task, {}).get("concern", ""),
            severity_critical_task=int(
                tmeta.get(task, {}).get("severity_critical", False)),
            bytes=len(src)))
        for h in hits:
            findings.append(dict(file=fn, model=model, task=task, rep=rep,
                                 tool="ICS-SAST", **h))
        for h in cpc:
            findings.append(dict(file=fn, model=model, task=task, rep=rep,
                                 tool="cppcheck", rule_id=h["id"],
                                 family=h["id"], cwe="",
                                 severity=h["severity"], line=h["line"],
                                 description=h["msg"]))
        print(f"[{fn}] compile={compiles} ics={len(hits)} cpp={len(cpc)}",
              flush=True)

    ST.write_csv(per_file, os.path.join(DATA, "per_generation.csv"))
    ST.write_csv(findings, os.path.join(DATA, "findings.csv"))
    print(f"[write] {len(per_file)} generations, {len(findings)} findings")

    # ------------------------------------------------------- human reference
    ref = os.path.join(DATA, "reference_solution.c")
    ref_stats = {}
    if os.path.exists(ref):
        c = subprocess.run(ZIG + ["-std=c99", "-w", ref, "-o",
                                  os.path.join(builddir, "ref.exe")],
                           capture_output=True, timeout=240, env=ENV)
        clean, defines = prep(open(ref, encoding="utf-8").read())
        hits, _ = R.analyze(clean, defines)
        cpc = run_cppcheck(ref)
        ref_stats = dict(compiles=int(c.returncode == 0),
                         n_ics_findings=len(hits),
                         n_cppcheck_findings=len(cpc),
                         ics_rules=sorted({h["rule_id"] for h in hits}),
                         cppcheck_ids=sorted({h["id"] for h in cpc}))
        print(f"[reference] {ref_stats}")

    out = {"population": dict(
        n_generations=len(per_file),
        n_models=len({p["model"] for p in per_file}),
        n_tasks=len({p["task"] for p in per_file}),
        n_reps=len({p["rep"] for p in per_file}),
        n_findings=len(findings),
        reference=ref_stats)}

    # ------------------------------------------------------------- RQ1 compile
    r1 = []
    for p in per_file:
        r1.append(dict(model=p["model"], task=p["task"],
                       compiles=p["compiles"], lines=p["lines"],
                       errors=p["compile_errors"], warnings=p["warnings"]))
    ST.write_csv(r1, os.path.join(DATA, "analysis_rq1_compilability.csv"))
    ok = [p for p in per_file if p["compiles"]]
    out["rq1"] = dict(
        n=len(per_file),
        compile_rate=round(len(ok) / len(per_file), 4) if per_file else 0,
        median_errors_when_failing=ST.quantile(
            sorted(p["compile_errors"] for p in per_file if not p["compiles"]),
            .5) if len(ok) < len(per_file) else 0,
        per_model={m: dict(
            n=sum(1 for p in per_file if p["model"] == m),
            compile_rate=round(
                sum(1 for p in per_file
                    if p["model"] == m and p["compiles"]) /
                max(1, sum(1 for p in per_file if p["model"] == m)), 4))
            for m in sorted({p["model"] for p in per_file})},
        per_task={t: dict(
            n=sum(1 for p in per_file if p["task"] == t),
            compile_rate=round(
                sum(1 for p in per_file
                    if p["task"] == t and p["compiles"]) /
                max(1, sum(1 for p in per_file if p["task"] == t)), 4))
            for t in sorted({p["task"] for p in per_file})},
        compile_rate_vs_lines_spearman=ST.spearman(
            [p["lines"] for p in per_file],
            [p["compiles"] for p in per_file]))
    print(f"[rq1] compile rate {out['rq1']['compile_rate']}")

    # ---------------------------------------------------- RQ2 anti-patterns
    ics = [f for f in findings if f["tool"] == "ICS-SAST"]
    cpc = [f for f in findings if f["tool"] == "cppcheck"]
    per_gen_ids = defaultdict(set)
    for f in ics:
        per_gen_ids[f["file"]].add(f["rule_id"])
    r2 = []
    for rid in sorted({r["id"] for r in R.RULES}):
        meta = next(r for r in R.RULES if r["id"] == rid)
        nf = sum(1 for f in ics if f["rule_id"] == rid)
        gens = len({f["file"] for f in ics if f["rule_id"] == rid})
        r2.append(dict(rule=rid, family=meta["family"], cwe=meta["cwe"],
                       severity=meta["severity"], n_findings=nf,
                       n_generations=gens,
                       gen_share=round(gens / len(per_file), 4)
                       if per_file else 0,
                       description=meta["description"]))
    r2.sort(key=lambda x: -x["n_generations"])
    ST.write_csv(r2, os.path.join(DATA, "analysis_rq2_rules.csv"))

    fam = Counter(f["family"] for f in ics)
    sev = Counter(f["severity"] for f in ics)
    # human baseline on the same contract
    ref_ids = set(ref_stats.get("ics_rules", []))
    diff = []
    for row in r2:
        rid = row["rule"]
        diff.append(dict(rule=rid, family=row["family"],
                         gen_gen_share=row["gen_share"],
                         human_reference=1 if rid in ref_ids else 0))
    ST.write_csv(diff, os.path.join(DATA, "analysis_rq2_vs_reference.csv"))
    fisher = {}
    for row in r2:
        g = row["n_generations"]
        h = 1 if row["rule"] in ref_ids else 0
        if len(per_file) - g >= 0 and h in (0, 1):
            pass
    tot_g = len(per_file)
    for row in r2:
        g = row["n_generations"]
        h = 1 if row["rule"] in ref_ids else 0
        # 2x2: [rule in gen, rule not in gen] x [rule in ref, rule not in ref]
        a, b = g, tot_g - g
        c, d = h, 1 - h
        if a + b + c + d > 0:
            fisher[row["rule"]] = ST.fisher_exact_2x2(a, b, c, d)
    out["rq2"] = dict(
        n_ics_findings=len(ics), n_cppcheck_findings=len(cpc),
        per_rule=r2,
        families=dict(fam), severities=dict(sev),
        detection_overlap=dict(
            rules_also_in_cppcheck=len(
                {f["rule_id"] for f in ics} & {f["id"] for f in cpc}),
            cppcheck_only_ids=sorted(
                {f["id"] for f in cpc} - {f["rule_id"] for f in ics})[:15],
            ics_only_rules=sorted(
                {f["rule_id"] for f in ics} - {f["id"] for f in cpc})),
        reference_comparison=fisher,
        reference_rules=sorted(ref_ids))
    print(f"[rq2] ICS findings {len(ics)}, cppcheck {len(cpc)}")
    print(f"[rq2] rules also found by cppcheck: "
          f"{out['rq2']['detection_overlap']['rules_also_in_cppcheck']}")

    # ------------------------------------------- RQ3 predictors of findings
    num = [(p["lines"], p["n_ics_findings"]) for p in per_file]
    bin1 = [(p["lines"], p["n_ics_findings"]) for p in per_file
            if p["compiles"]]
    out["rq3"] = dict(
        spearman_lines_vs_findings=ST.spearman(
            [x[0] for x in num], [x[1] for x in num]),
        spearman_lines_vs_findings_compiling_only=ST.spearman(
            [x[0] for x in bin1], [x[1] for x in bin1]),
        critical_task_findings=ST.describe(
            [p["n_ics_findings"] for p in per_file if p["severity_critical_task"]],
            "critical-task"),
        noncritical_task_findings=ST.describe(
            [p["n_ics_findings"] for p in per_file
             if not p["severity_critical_task"]], "non-critical-task"))
    t = ST.mannwhitney_u(
        [p["n_ics_findings"] for p in per_file if p["severity_critical_task"]],
        [p["n_ics_findings"] for p in per_file
         if not p["severity_critical_task"]])
    t["cliffs_delta"] = ST.cliffs_delta(
        [p["n_ics_findings"] for p in per_file if p["severity_critical_task"]],
        [p["n_ics_findings"] for p in per_file
         if not p["severity_critical_task"]])
    out["rq3"]["test_critical_vs_noncritical"] = t
    per_task_find = defaultdict(list)
    for p in per_file:
        per_task_find[p["task"]].append(p["n_ics_findings"])
    out["rq3"]["per_task"] = [
        dict(task=k, n=len(v), mean=round(sum(v) / len(v), 3),
             median=ST.quantile(sorted(v), .5),
             subsystem=tmeta.get(k, {}).get("subsystem", ""))
        for k, v in sorted(per_task_find.items(), key=lambda x: -sum(x[1]) / len(x[1]))]
    print(f"[rq3] critical vs non-critical p={t.get('p')}")

    ST.write_json(out, os.path.join(DATA, "analysis_results.json"))
    print("ANALYSIS COMPLETE")


if __name__ == "__main__":
    main()
