"""Launcher for the SQJ analysis, kept as a file so the shell never has to
carry the script body (a long `-c` argument was being killed before the
interpreter started)."""
import importlib.util
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "..", "00_shared"))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

spec = importlib.util.spec_from_file_location(
    "sqj_analysis", os.path.join(ROOT, "scripts", "run_analysis.py"))
mod = importlib.util.module_from_spec(spec)
print("[launch] loading analysis module", flush=True)
spec.loader.exec_module(mod)
print("[launch] module loaded; generated files:",
      len([f for f in os.listdir(mod.GEN) if f.endswith(".c")]), flush=True)
print("[launch] running main", flush=True)
mod.main()
print("[launch] done", flush=True)
