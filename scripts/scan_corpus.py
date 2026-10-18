"""Static-analysis pass over the generated corpus.

Split from the statistics pass on purpose: this stage is the one that shells
out to `zig cc` and `cppcheck`, and running it as its own process keeps a
failure in either external tool from taking the reporting stage down with it.
Every generation is analysed three ways, mirroring compile_taxonomy.py:
  1. as generated,
  2. with the headers the system prompt omitted injected,
  3. with a user `main` removed,
so that a finding can be attributed to the model rather than to the harness.
"""
import os
import re
import sys
import csv
import json
import subprocess
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "data")
GEN = os.path.join(DATA, "generated")
TABLES = os.path.join(DATA, "analysis_out")
BUILD = os.path.join(TABLES, "build")
os.makedirs(BUILD, exist_ok=True)

sys.path.insert(0, os.path.join(ROOT, "..", "00_shared"))
sys.path.insert(0, HERE)
import stats_core as ST  # noqa: E402
import ics_rules as R  # noqa: E402

CPPCHECK = os.path.join(os.path.dirname(sys.executable), "cppcheck.exe")
ENV = dict(os.environ,
           ZIG_GLOBAL_CACHE_DIR=os.path.join(ROOT, "..", ".zigcache"))
SHIM = "#include <stdio.h>\n#include <stdlib.h>\n#include <string.h>\n"


def strip_comments(s):
    s = re.sub(r"/\*.*?\*/", " ", s, flags=re.S)
    return re.sub(r"//[^\n]*", " ", s)


def strip_strings(s):
    return re.sub(r'"(\\.|[^"\\])*"', '""', s)


def defines_of(s):
    d = {}
    for m in re.finditer(r"^\s*#\s*define\s+([A-Za-z_]\w*)\s+(.+?)\s*$", s, re.M):
        d[m.group(1)] = m.group(2).strip()
    return d


def strip_main(src):
    m = re.search(r"\bint\s+main\s*\(", src)
    if not m:
        return src
    start = src.rfind("\n", 0, m.start()) + 1
    j, depth, seen = m.end(), 0, False
    end = j
    for k in range(j, len(src)):
        if src[k] == "(":
            depth += 1
            seen = True
        elif src[k] == ")":
            depth -= 1
            if seen and depth == 0:
                end = k
                break
    b = src.find("{", end)
    if b < 0:
        return src[:start]
    d = 0
    for p in range(b, len(src)):
        if src[p] == "{":
            d += 1
        elif src[p] == "}":
            d -= 1
            if d == 0:
                return src[:start] + src[p + 1:]
    return src[:start]


def cppcheck(path):
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
    out = []
    for line in txt.splitlines():
        p = line.split("|", 3)
        if len(p) == 4 and p[0].strip():
            try:
                ln = int(p[3].strip())
            except ValueError:
                ln = 0
            out.append(dict(severity=p[0].strip(), id=p[1].strip(),
                            msg=p[2].strip(), line=ln))
    return out


def main():
    files = sorted(f for f in os.listdir(GEN) if f.endswith(".c"))
    if not files:
        print("no generated corpus")
        return
    tj = os.path.join(DATA, "taskset.json")
    tmeta = {}
    if os.path.exists(tj):
        tmeta = {t["id"]: t for t in
                 json.load(open(tj, encoding="utf-8"))["tasks"]}
    print(f"[scan] {len(files)} generations", flush=True)

    per_file, findings = [], []
    for k, fn in enumerate(files):
        path = os.path.join(GEN, fn)
        src = open(path, encoding="utf-8", errors="ignore").read()
        parts = fn[:-2].split("__")
        model = parts[0] if parts else "?"
        task = parts[1] if len(parts) > 1 else "?"
        rep = parts[2] if len(parts) > 2 else "?"

        clean = strip_strings(strip_comments(src))
        defs = defines_of(clean)
        hits, ctx = R.analyze(clean, defs)
        nomain = strip_main(src)
        nclean = strip_strings(strip_comments(nomain))
        nhits, nctx = R.analyze(nclean, defines_of(nclean))

        # ICS-SAST on a compilable variant: a rule that only fires on code the
        # compiler rejects is not actionable, so both counts are reported
        shim_path = os.path.join(BUILD, fn[:-2] + "_sh.c")
        with open(shim_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(SHIM + nomain)
        cpc = cppcheck(shim_path)
        cpc_ids = Counter(h["id"] for h in cpc)
        cpc_sev = Counter(h["severity"] for h in cpc)

        per_file.append(dict(
            file=fn, model=model, task=task, rep=rep,
            subsystem=tmeta.get(task, {}).get("subsystem", ""),
            concern=tmeta.get(task, {}).get("concern", ""),
            severity_critical_task=int(
                tmeta.get(task, {}).get("severity_critical", False)),
            lines=len(src.splitlines()),
            n_functions=len(ctx["funcs"]) if ctx else 0,
            ics_findings=len(hits),
            ics_findings_no_main=len(nhits),
            ics_critical=sum(1 for h in hits if h["severity"] == "critical"),
            ics_high=sum(1 for h in hits if h["severity"] == "high"),
            ics_medium=sum(1 for h in hits if h["severity"] == "medium"),
            ics_families=";".join(
                f"{k}:{v}" for k, v in Counter(
                    h["family"] for h in hits).most_common()),
            ics_rules=";".join(sorted({h["rule_id"] for h in hits})),
            cppcheck_findings=len(cpc),
            cppcheck_ids=";".join(f"{k}:{v}" for k, v in cpc_ids.most_common(6)),
            cppcheck_error=int(cpc_sev.get("error", 0)),
            cppcheck_warning=int(cpc_sev.get("warning", 0)),
            cppcheck_style=int(cpc_sev.get("style", 0)),
            cppcheck_portability=int(cpc_sev.get("portability", 0)),
            has_main=int(bool(re.search(r"\bint\s+main\s*\(", src))),
            uses_float=int(bool(re.search(r"\b(float|double)\b", src))),
            uses_malloc=int(bool(re.search(r"\b(malloc|calloc|free)\s*\(", src))),
        ))
        for h in hits:
            findings.append(dict(file=fn, model=model, task=task, rep=rep,
                                 tool="ICS-SAST", **h))
        for h in cpc:
            findings.append(dict(file=fn, model=model, task=task, rep=rep,
                                 tool="cppcheck", rule_id=h["id"],
                                 family=h["id"], cwe="", severity=h["severity"],
                                 line=h["line"], description=h["msg"]))
        print(f"[{k+1}/{len(files)}] {fn}: ics={len(hits)} "
              f"({len(nhits)} w/o main) cpp={len(cpc)}", flush=True)

    p1 = os.path.join(TABLES, "per_generation.csv")
    with open(p1, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(per_file[0].keys()))
        w.writeheader()
        w.writerows(per_file)
    print(f"[write] {p1} n={len(per_file)}")

    p2 = os.path.join(TABLES, "findings.csv")
    with open(p2, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["file", "model", "task", "rep",
                                          "tool", "rule_id", "family", "cwe",
                                          "severity", "line", "description"])
        w.writeheader()
        w.writerows(findings)
    print(f"[write] {p2} n={len(findings)}")
    print("SCAN COMPLETE")


if __name__ == "__main__":
    main()
