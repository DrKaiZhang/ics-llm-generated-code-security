#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
02_SQJ_llm_secure_antipatterns / generate_code.py

Batch generation of industrial-control C code by locally executed open-weight
code LLMs. Each (model, task) pair is sampled with a fixed seed and a fixed
decoding configuration so the study is reproducible. Generations are written
as standalone compilable translation units.

Why local models: the study needs many samples per model and full control of
decoding parameters; local CPU execution gives both without external quota.
Models are recorded with their exact revision hashes in models.json.
"""
import os
import re
import sys
import json
import time
import argparse
import multiprocessing

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "data")
GEN = os.path.join(DATA, "generated")
os.makedirs(GEN, exist_ok=True)

MODELS = {
    "qwen2.5-coder-0.5b": "Qwen/Qwen2.5-Coder-0.5B-Instruct",
    "qwen2.5-coder-1.5b": "Qwen/Qwen2.5-Coder-1.5B-Instruct",
}

# Resolve the weights to a local directory once, so worker processes never
# touch the Hugging Face cache (which is not readable from every process
# context and is a source of lock contention).
LOCAL_PATHS = {}


def resolve_model(repo_id):
    if repo_id in LOCAL_PATHS:
        return LOCAL_PATHS[repo_id]
    from huggingface_hub import snapshot_download
    p = snapshot_download(repo_id, allow_patterns=[
        "*.json", "*.safetensors", "tokenizer*", "vocab*", "merges*"])
    LOCAL_PATHS[repo_id] = p
    return p

SYSTEM = (
    "You are a senior embedded systems engineer writing safety-relevant "
    "industrial control code in C99. Answer with a single self-contained "
    "C translation unit. Use only #include <stdint.h>, <stddef.h>, <stdbool.h> "
    "and <string.h>. No dynamic allocation, no floating point unless the "
    "request allows it. Reply with code only: no prose, no markdown fences."
)


def extract_code(text):
    """Strip fences / prose, keep the first complete translation unit."""
    t = text.strip()
    m = re.search(r"```(?:c|c99|cpp)?\s*\n(.*?)(?:```|\Z)", t, re.S)
    if m:
        t = m.group(1)
    # drop leading prose lines before the first preprocessor/#include/type decl
    lines = t.splitlines()
    start = 0
    for i, l in enumerate(lines):
        if re.match(r"\s*(#include|#define|typedef|static|int|void|uint|int\d+_t|"
                    r"bool|char|float|double|extern|enum|struct|#)", l):
            start = i
            break
    else:
        start = 0
    code = "\n".join(lines[start:]).strip()
    # remove a trailing unmatched brace
    if code.count("{") > code.count("}"):
        idx = code.rfind("}")
        if idx > 0:
            code = code[:idx + 1]
    return code + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="qwen2.5-coder-0.5b")
    ap.add_argument("--reps", type=int, default=8)
    ap.add_argument("--max-new-tokens", type=int, default=640)
    ap.add_argument("--temperature", type=float, default=0.8)
    ap.add_argument("--seed", type=int, default=20260101)
    ap.add_argument("--tasks", default="")
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--local-path", default="")
    args = ap.parse_args()

    if not args.local_path:
        args.local_path = resolve_model(MODELS[args.model])
    print(f"[model] {args.model} -> {args.local_path}", flush=True)

    tasks = json.load(open(os.path.join(DATA, "taskset.json"), encoding="utf-8"))
    task_list = tasks["tasks"]
    if args.tasks:
        want = set(args.tasks.split(","))
        task_list = [t for t in task_list if t["id"] in want]

    # build the full job list first, then run it across worker processes
    jobs = []
    for t in task_list:
        for rep in range(args.reps):
            out_path = os.path.join(GEN, f"{args.model}__{t['id']}__r{rep}.c")
            if os.path.exists(out_path) and os.path.getsize(out_path) > 40:
                continue
            jobs.append((t, rep, out_path))
    if not jobs:
        print(f"GEN COMPLETE {args.model}: nothing to do")
        return
    print(f"[plan] {args.model}: {len(jobs)} generations, "
          f"{args.workers} workers", flush=True)

    # Each worker loads the model once; torch is restricted to one thread so the
    # processes do not oversubscribe the 12 available cores.
    chunks = [jobs[i::args.workers] for i in range(args.workers)]
    procs = []
    for wi, chunk in enumerate(chunks):
        if not chunk:
            continue
        p = multiprocessing.Process(target=worker,
                                    args=(wi, args, chunk))
        p.start()
        procs.append(p)
    for p in procs:
        p.join()
    done = len([f for f in os.listdir(GEN) if f.startswith(args.model)])
    print(f"GEN COMPLETE {args.model}: files_now={done}")


SYSTEM = (
    "You are a senior embedded systems engineer writing safety-relevant "
    "industrial control code in C99. Answer with a single self-contained "
    "C translation unit. Use only #include <stdint.h>, <stddef.h>, <stdbool.h> "
    "and <string.h>. No dynamic allocation, no floating point unless the "
    "request allows it. Reply with code only: no prose, no markdown fences."
)


def worker(wid, args, jobs):
    import torch
    # Each worker holds a full float32 copy of the weights. On CPU that is
    # ~2 GB for the 0.5B model and ~6 GB for the 1.5B model, so the worker
    # count is deliberately small and threads are capped.
    torch.set_num_threads(3)
    from transformers import AutoTokenizer, AutoModelForCausalLM
    mid = args.model
    repo = MODELS[mid]
    path = args.local_path
    tok = AutoTokenizer.from_pretrained(path, local_files_only=True)
    # bfloat16 keeps CPU inference numerically sane at roughly half the memory
    # of float32; on a memory-constrained host float32 loads caused the worker
    # to be killed before producing a single sample.
    try:
        model = AutoModelForCausalLM.from_pretrained(
            path, dtype=torch.bfloat16, low_cpu_mem_usage=True,
            local_files_only=True)
    except Exception:
        model = AutoModelForCausalLM.from_pretrained(
            path, dtype=torch.float32, low_cpu_mem_usage=True,
            local_files_only=True)
    model.eval()
    if wid == 0:
        meta_path = os.path.join(DATA, "models.json")
        meta = json.load(open(meta_path, encoding="utf-8")) \
            if os.path.exists(meta_path) else {}
        meta[mid] = dict(
            hf_repo=repo, revision=getattr(model.config, "_commit_hash", None),
            params="0.5B" if "0.5" in mid else "1.5B", dtype="float32",
            device="cpu", workers=args.workers,
            decoding=dict(temperature=args.temperature, top_p=0.95,
                          max_new_tokens=args.max_new_tokens,
                          reps_per_task=args.reps, seed=args.seed))
        json.dump(meta, open(meta_path, "w", encoding="utf-8"), indent=2)

    for t, rep, out_path in jobs:
        torch.manual_seed(args.seed + 1000 * rep + int(t["id"][1:]))
        msgs = [{"role": "system", "content": SYSTEM},
                {"role": "user", "content": t["prompt"]}]
        text = tok.apply_chat_template(msgs, tokenize=False,
                                       add_generation_prompt=True)
        ids = tok(text, return_tensors="pt")
        with torch.no_grad():
            out = model.generate(
                **ids, max_new_tokens=args.max_new_tokens,
                do_sample=True, temperature=args.temperature, top_p=0.95,
                pad_token_id=tok.eos_token_id)
        gen = tok.decode(out[0][ids["input_ids"].shape[1]:],
                         skip_special_tokens=True)
        code = extract_code(gen)
        with open(out_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(f"/* model={mid} task={t['id']} rep={rep} "
                    f"seed={args.seed} */\n")
            f.write(code)
        print(f"[w{wid}] {t['id']} rep{rep} -> {len(code)}B", flush=True)


if __name__ == "__main__":
    main()
