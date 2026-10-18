"""Stepwise probe for the SQJ analysis pipeline.

Each stage is guarded so the last printed line identifies exactly where the
process dies. Written as a file because a long `-c` argument was itself being
terminated before the interpreter started.
"""
import csv
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "data")
GEN = os.path.join(DATA, "generated")
TABLES = os.path.join(DATA, "analysis_out")
os.makedirs(TABLES, exist_ok=True)
sys.path.insert(0, os.path.join(ROOT, "..", "00_shared"))
sys.path.insert(0, HERE)

print("A: paths resolved", flush=True)
import stats_core as ST  # noqa: E402
print("B: stats_core imported", flush=True)
import ics_rules as R  # noqa: E402
print("C: ics_rules imported", flush=True)

CPPCHECK = os.path.join(os.path.dirname(sys.executable), "cppcheck.exe")
ZIG = [sys.executable, "-m", "ziglang", "cc"]
ENV = dict(os.environ,
           ZIG_GLOBAL_CACHE_DIR=os.path.join(ROOT, "..", ".zigcache"))

files = sorted(f for f in os.listdir(GEN) if f.endswith(".c"))
print(f"D: {len(files)} generated files", flush=True)

tasks = json_tasks = None
tj = os.path.join(DATA, "taskset.json")
if os.path.exists(tj):
    import json
    json_tasks = json.load(open(tj, encoding="utf-8"))["tasks"]
    tasks = {t["id"]: t for t in json_tasks}
    print(f"E: task set loaded ({len(tasks)} tasks)", flush=True)

builddir = os.path.join(TABLES, "build")
os.makedirs(builddir, exist_ok=True)
print("F: build dir ready", flush=True)

okc = 0
for k, fn in enumerate(files):
    path = os.path.join(GEN, fn)
    exe = os.path.join(builddir, fn[:-2] + ".exe")
    try:
        c = subprocess.run(ZIG + ["-std=c99", "-w", path, "-o", exe],
                           capture_output=True, timeout=240, env=ENV)
        compiles = c.returncode == 0
    except Exception as e:
        print(f"G: compile EXCEPTION on {fn}: {e}", flush=True)
        continue
    okc += compiles
    print(f"G{ k+1}/{len(files)}: {fn} compiles={compiles}", flush=True)
print(f"H: compiled {okc}/{len(files)}", flush=True)
print("PROBE COMPLETE", flush=True)
