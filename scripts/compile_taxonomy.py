"""Compilation-outcome taxonomy for the generated corpus.

The first full run showed 0/15 compilable, so this script classifies *why*:
the failure reason is the reportable result, not an obstacle. Each generated
file is compiled once and its diagnostics are mapped to a cause category, with
an optional shim (auto-injecting the headers the system prompt did not name)
so that a missing include is separated from a genuine code defect.
"""
import os
import re
import json
import csv
import subprocess
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "data")
GEN = os.path.join(DATA, "generated")
TABLES = os.path.join(DATA, "analysis_out")
os.makedirs(TABLES, exist_ok=True)

ZIG = [sys.executable, "-m", "ziglang", "cc"]
ENV = dict(os.environ,
           ZIG_GLOBAL_CACHE_DIR=os.path.join(ROOT, "..", ".zigcache"))
BUILD = os.path.join(TABLES, "build")
os.makedirs(BUILD, exist_ok=True)

# The system prompt names only these headers, so a generated file that calls
# printf without <stdio.h> is a *prompt-induced* failure, not a logic error.
SHIM = "#include <stdio.h>\n#include <stdlib.h>\n#include <string.h>\n"

CATEGORIES = [
    ("missing-include",
     r"undeclared (?:library )?function|implicit function declaration|"
     r"include the header|undeclared identifier"),
    ("unknown-type",
     r"unknown type name|unknown type|invalid type|"
     r"cannot find (?:type|definition)"),
    ("undeclared-symbol",
     r"use of undeclared identifier|undeclared identifier"),
    ("syntax-error", r"syntax error|expected .*;|expected .*}"),
    ("linkage-missing", r"undefined (?:reference|symbol)|linker error"),
    ("type-mismatch", r"incompatible (?:pointer|operand|types)|"
                      r"cannot convert|passing .* to parameter"),
    ("array-bounds", r"array index|subscript|out of bounds|"
                     r"variable length array"),
    ("redefinition", r"redefinition|redeclared"),
    ("other-error", r"error:"),
]


def categorise(stderr):
    if not stderr.strip():
        return "no-diagnostics"
    for name, rx in CATEGORIES:
        if re.search(rx, stderr, re.I):
            return name
    return "unclassified"


def first_error(stderr):
    m = re.search(r"error: (.*)", stderr)
    return m.group(1)[:160] if m else ""


def compile_one(path, out, source_text):
    try:
        c = subprocess.run(ZIG + ["-std=c99", "-w", source_text and path or path,
                                  "-o", out],
                           capture_output=True, timeout=240, env=ENV)
    except Exception as e:
        return False, "", f"exception: {e}"
    err = c.stderr.decode("utf-8", "replace")
    return c.returncode == 0, err, ""


def compile_text(text, out, name):
    p = os.path.join(BUILD, name + ".c")
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    try:
        c = subprocess.run(ZIG + ["-std=c99", "-w", p, "-o", out],
                           capture_output=True, timeout=240, env=ENV)
    except Exception as e:
        return False, "", f"exception: {e}"
    return c.returncode == 0, c.stderr.decode("utf-8", "replace"), ""


def strip_main(src):
    """Remove a user `main` so a translation unit can be linked into a harness."""
    out, depth, i = [], 0, 0
    m = re.search(r"\bint\s+main\s*\(", src)
    if not m:
        return src
    start = src.rfind("\n", 0, m.start()) + 1
    j, depth, seen = m.end(), 0, False
    for k in range(j, len(src)):
        if src[k] == "(":
            depth += 1
            seen = True
        elif src[k] == ")":
            depth -= 1
            if seen and depth == 0:
                break
    k = src.find("{", j)
    if k < 0:
        return src[:start]
    d = 0
    for p in range(k, len(src)):
        if src[p] == "{":
            d += 1
        elif src[p] == "}":
            d -= 1
            if d == 0:
                return src[:start] + src[p + 1:]
    return src[:start]


def main():
    files = sorted(f for f in os.listdir(GEN) if f.endswith(".c"))
    if not files:
        print("no generated corpus")
        return
    tasks = {}
    tj = os.path.join(DATA, "taskset.json")
    if os.path.exists(tj):
        tasks = {t["id"]: t for t in
                 json.load(open(tj, encoding="utf-8"))["tasks"]}

    rows = []
    for fn in files:
        path = os.path.join(GEN, fn)
        src = open(path, encoding="utf-8", errors="ignore").read()
        parts = fn[:-2].split("__")
        model = parts[0] if parts else "?"
        task = parts[1] if len(parts) > 1 else "?"
        rep = parts[2] if len(parts) > 2 else "?"

        raw_ok, raw_err, _ = compile_one(path, os.path.join(BUILD,
                                                            fn[:-2] + ".exe"),
                                         src)
        cat = "compiles" if raw_ok else categorise(raw_err)

        # second attempt: inject the headers the system prompt omitted
        shimmed = SHIM + src
        shim_ok, shim_err, _ = compile_text(
            shimmed, os.path.join(BUILD, fn[:-2] + "_shim.exe"),
            fn[:-2] + "_shim")

        # third attempt: also drop a user main
        nomain = SHIM + strip_main(src)
        nm_ok, nm_err, _ = compile_text(
            nomain, os.path.join(BUILD, fn[:-2] + "_nm.exe"), fn[:-2] + "_nm")

        rows.append(dict(
            file=fn, model=model, task=task, rep=rep,
            subsystem=tasks.get(task, {}).get("subsystem", ""),
            concern=tasks.get(task, {}).get("concern", ""),
            lines=len(src.splitlines()), bytes=len(src),
            compiles_raw=int(raw_ok), category=cat,
            first_error=first_error(raw_err),
            n_errors=len(re.findall(r"error:", raw_err)),
            compiles_with_include_shim=int(shim_ok),
            shim_category="compiles" if shim_ok else categorise(shim_err),
            compiles_with_shim_and_no_main=int(nm_ok),
            nm_category="compiles" if nm_ok else categorise(nm_err),
            has_main=int(bool(re.search(r"\bint\s+main\s*\(", src))),
        ))
        print(f"{fn}: raw={raw_ok}({cat}) shim={shim_ok} nomain={nm_ok}",
              flush=True)

    p = os.path.join(TABLES, "compile_taxonomy.csv")
    with open(p, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"[write] {p} n={len(rows)}")

    cat = Counter(r["category"] for r in rows)
    shim = Counter(r["shim_category"] for r in rows)
    summ = dict(
        n=len(rows),
        compiles_raw=sum(r["compiles_raw"] for r in rows),
        compiles_with_shim=sum(r["compiles_with_include_shim"] for r in rows),
        compiles_with_shim_no_main=sum(
            r["compiles_with_shim_and_no_main"] for r in rows),
        categories_raw=dict(cat.most_common()),
        categories_with_shim=dict(shim.most_common()),
        has_main=sum(r["has_main"] for r in rows),
        median_lines=sorted(r["lines"] for r in rows)[len(rows) // 2])
    out = os.path.join(TABLES, "compile_taxonomy.json")
    json.dump(summ, open(out, "w", encoding="utf-8"), indent=2,
              ensure_ascii=False)
    print("[summary]", json.dumps(summ, ensure_ascii=False, indent=2))
    print("TAXONOMY COMPLETE")


if __name__ == "__main__":
    main()
