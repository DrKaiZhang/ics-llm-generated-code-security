#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
02_SQJ_llm_secure_antipatterns / validate_rules.py

Rule-set validation study. A paired validation corpus is constructed: for each
ICS concern we provide a *vulnerable* variant and a *guarded* variant that
differs only in the added validation. Both variants are compiled (zig cc,
-std=c99 -Wall -Wextra) and executed against a shared functional test, so a
variant only counts as "functionally correct" if it still passes the test.
This yields a measurable per-rule discrimination profile for the paper:

    sensitivity  = hits(vulnerable)   / n vulnerable samples carrying the rule
    specificity  = misses(guarded)    -> reported on guarded = false positive

Outputs: data/rule_validation.csv, data/rule_validation_summary.csv
"""
import os
import re
import sys
import csv
import json
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ics_rules as R  # noqa: E402

ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "data")
VAL = os.path.join(ROOT, "data", "validation")
os.makedirs(VAL, exist_ok=True)

ZIG = [sys.executable, "-m", "ziglang", "cc"]
ENV = dict(os.environ, ZIG_GLOBAL_CACHE_DIR=os.path.join(ROOT, "..", ".zigcache"))


def prep(src):
    s = re.sub(r"/\*.*?\*/", " ", src, flags=re.S)
    s = re.sub(r"//[^\n]*", " ", s)
    s = re.sub(r'"(\\.|[^"\\])*"', '""', s)
    d = {}
    for m in re.finditer(r"^\s*#\s*define\s+([A-Za-z_]\w*)\s+(.+?)\s*$", s, re.M):
        d[m.group(1)] = m.group(2).strip()
    return s, d


# Each case: (case_id, concern, rules_expected, vulnerable_src, guarded_src,
#             test_main)
CASES = []


def case(cid, concern, rules, vuln, guarded, test):
    CASES.append((cid, concern, rules, vuln, guarded, test))


HARNESS = r"""
#include <stdio.h>
#include <stdint.h>
static int fails = 0;
#define CHECK(c) do { if (!(c)) { printf("check failed at line %d\n", __LINE__); fails++; } } while (0)
int main(void) {
%s
    if (fails == 0) { printf("ALLPASS\n"); return 0; }
    printf("FAILED %d\n", fails);
    return 1;
}
"""

case(
    "V01", "unchecked buffer copy fed by a protocol length", ["ICS01"],
    r'''
#include <stdint.h>
#include <string.h>
#define MAXD 32
static uint8_t dst[MAXD];
int store(const uint8_t *src, uint16_t n)
{
    memcpy(dst, src, n);
    return (int)dst[0];
}
''',
    r'''
#include <stdint.h>
#include <string.h>
#define MAXD 32
static uint8_t dst[MAXD];
int store(const uint8_t *src, uint16_t n)
{
    if (n > (uint16_t)MAXD) { return -1; }
    memcpy(dst, src, n);
    return (int)dst[0];
}
''',
    r'''
    uint8_t in[64]; int i;
    for (i = 0; i < 64; i++) { in[i] = (uint8_t)i; }
    CHECK(store(in, 8u) == 0);
    CHECK(store(in, 40u) == -1);      /* only the guarded variant can pass:
                                         the vulnerable one overwrites past dst */
''')

case(
    "V02", "division by an unvalidated divisor", ["ICS02"],
    r'''
#include <stdint.h>
int32_t ratio(uint16_t raw, int16_t span, int16_t n)
{
    return ((int32_t)raw * (int32_t)span) / n;
}
''',
    r'''
#include <stdint.h>
int32_t ratio(uint16_t raw, int16_t span, int16_t n)
{
    if (n == 0) { return 0; }
    return ((int32_t)raw * (int32_t)span) / (int32_t)n;
}
''',
    r'''
    CHECK(ratio(100, 10, 4) == 250);
    CHECK(ratio(100, 10, 0) == 0);
''')

case(
    "V03", "unclamped integral accumulator in a control loop", ["ICS04", "ICS08"],
    r'''
#include <stdint.h>
static int32_t integ;
int16_t pid(int16_t setp, int16_t meas, int16_t kp, int16_t ki)
{
    int32_t err = (int32_t)setp - (int32_t)meas;
    integ = integ + ((int32_t)ki * err) / 100;
    return (int16_t)(((int32_t)kp * err) / 100 + integ);
}
''',
    r'''
#include <stdint.h>
static int32_t integ;
int16_t pid(int16_t setp, int16_t meas, int16_t kp, int16_t ki)
{
    int32_t err = (int32_t)setp - (int32_t)meas;
    integ = integ + ((int32_t)ki * err) / 100;
    if (integ > 32767) { integ = 32767; }
    if (integ < -32768) { integ = -32768; }
    return (int16_t)(((int32_t)kp * err) / 100 + integ);
}
''',
    r'''
    int i; int16_t y;
    for (i = 0; i < 50; i++) { y = pid(1000, 0, 100, 4000); }
    CHECK(y == 32767);
''')

case(
    "V04", "actuator command written without saturation", ["ICS08"],
    r'''
#include <stdint.h>
uint8_t g_duty;
void set_duty(int16_t cmd)
{
    g_duty = (uint8_t)cmd;
}
''',
    r'''
#include <stdint.h>
uint8_t g_duty;
void set_duty(int16_t cmd)
{
    if (cmd < 0) { cmd = 0; }
    if (cmd > 100) { cmd = 100; }
    g_duty = (uint8_t)cmd;
}
''',
    r'''
    set_duty(55);  CHECK(g_duty == 55);
    set_duty(250); CHECK(g_duty <= 100);
''')

case(
    "V05", "index derived from external input without a capacity check",
    ["ICS03", "ICS06"],
    r'''
#include <stdint.h>
#define NB 8
static uint16_t slots[NB];
uint16_t get(uint8_t i)
{
    return slots[i];
}
''',
    r'''
#include <stdint.h>
#define NB 8
static uint16_t slots[NB];
uint16_t get(uint8_t i)
{
    if (i >= NB) { return 0u; }
    return slots[i];
}
''',
    r'''
    int i;
    for (i = 0; i < NB; i++) { slots[i] = (uint16_t)(i * 2); }
    CHECK(get(3) == 6u);
    CHECK(get(200) == 0u);
''')

case(
    "V06", "loop trip count taken from an input length with no bound",
    ["ICS06"],
    r'''
#include <stdint.h>
#define CAP 64
static uint8_t sum(const uint8_t *b, uint16_t n)
{
    uint16_t i; uint8_t s = 0;
    for (i = 0; i < n; i++) { s = (uint8_t)(s + b[i]); }
    return s;
}
''',
    r'''
#include <stdint.h>
#define CAP 64
static uint8_t sum(const uint8_t *b, uint16_t n)
{
    uint16_t i; uint8_t s = 0;
    if (n > CAP) { return 0u; }
    for (i = 0; i < n; i++) { s = (uint8_t)(s + b[i]); }
    return s;
}
''',
    r'''
    uint8_t b[16]; int i;
    for (i = 0; i < 16; i++) { b[i] = 1u; }
    CHECK(sum(b, 4u) == 4u);
''')

case(
    "V07", "safety-relevant call whose result is discarded", ["ICS12"],
    r'''
#include <stdint.h>
static uint8_t reg;
int write_reg(uint8_t v) { reg = v; return (v == 0x5Au) ? 0 : -1; }
int commit(uint8_t v)
{
    write_reg(v);
    return 0;
}
''',
    r'''
#include <stdint.h>
static uint8_t reg;
int write_reg(uint8_t v) { reg = v; return (v == 0x5Au) ? 0 : -1; }
int commit(uint8_t v)
{
    if (write_reg(v) != 0) { return -1; }
    return 0;
}
''',
    r'''
    CHECK(commit(0x5Au) == 0);
    CHECK(commit(0x01u) == -1);
''')

case(
    "V08", "shift by a runtime amount", ["ICS10"],
    r'''
#include <stdint.h>
uint8_t extract(uint32_t word, uint8_t pos)
{
    return (uint8_t)((word >> pos) & 0xFFu);
}
''',
    r'''
#include <stdint_t>
uint8_t extract(uint32_t word, uint8_t pos)
{
    if (pos > 24u) { return 0u; }
    return (uint8_t)((word >> pos) & 0xFFu);
}
'''.replace("#include <stdint_t>", "#include <stdint.h>"),
    r'''
    CHECK(extract(0x12345678u, 8u) == 0x56u);
    CHECK(extract(0x12345678u, 200u) == 0u);
''')

case(
    "V09", "no input validation at all in a setpoint consumer", ["ICS05"],
    r'''
#include <stdint.h>
int16_t to_mA(int16_t pct)
{
    return (int16_t)(4000 + (pct * 16000) / 100);
}
''',
    r'''
#include <stdint.h>
int16_t to_mA(int16_t pct)
{
    if (pct < 0) { pct = 0; }
    if (pct > 100) { pct = 100; }
    return (int16_t)(4000 + ((int32_t)pct * 16000) / 100);
}
''',
    r'''
    CHECK(to_mA(0) == 4000);
    CHECK(to_mA(100) == 20000);
    CHECK(to_mA(200) == 20000);
''')

case(
    "V10", "unsynchronised read-modify-write on shared ISR state", ["ICS07"],
    r'''
#include <stdint.h>
/* updated from a 1 kHz control ISR and read from the task context */
static volatile int32_t total;
int32_t add(int32_t v)
{
    total += v;
    return total;
}
''',
    r'''
#include <stdint.h>
/* updated from a 1 kHz control ISR under a critical section */
static void disable_irq(void);
static void enable_irq(void);
static volatile int32_t total;
int32_t add(int32_t v)
{
    int32_t prev;
    disable_irq();
    prev = total;
    total = prev + v;
    enable_irq();
    return total;
}
static void disable_irq(void) { }
static void enable_irq(void) { }
''',
    r'''
    CHECK(add(5) == 5);
    CHECK(add(7) == 12);
''')


def compile_and_run(name, unit_src, test_body):
    path = os.path.join(VAL, name + ".c")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(unit_src)
        f.write(HARNESS.replace("%s", test_body))
    exe = os.path.join(VAL, name + ".exe")
    c = subprocess.run(ZIG + ["-std=c99", path, "-o", exe],
                       capture_output=True, timeout=180, env=ENV)
    if c.returncode != 0:
        return dict(compile="fail", run="skip", passed=0,
                    stderr=c.stderr.decode("utf-8", "replace")[:400])
    try:
        r = subprocess.run([exe], capture_output=True, timeout=60)
        out = r.stdout.decode("utf-8", "replace")
    except Exception:
        return dict(compile="ok", run="fail", passed=0, stderr="timeout")
    return dict(compile="ok",
                run="ok" if r.returncode == 0 else "assert",
                passed=1 if "ALLPASS" in out else 0,
                stderr=out.strip()[:200])


def main():
    rows = []
    for cid, concern, rules, vuln, guarded, test in CASES:
        for variant, src in (("vulnerable", vuln), ("guarded", guarded)):
            fn = f"{cid}_{variant}"
            build = compile_and_run(fn, src, test)
            clean, defines = prep(src)
            hits, _ = R.analyze(clean, defines)
            ids = sorted({h["rule_id"] for h in hits})
            rows.append(dict(
                case_id=cid, concern=concern, variant=variant,
                expected_rules=";".join(rules), reported_rules=";".join(ids),
                n_findings=len(hits),
                compile=build["compile"], run=build["run"],
                functional_pass=build["passed"], build_log=build["stderr"]))
            print(f"[{cid}/{variant}] compile={build['compile']} "
                  f"pass={build['passed']} rules={','.join(ids) or '-'}",
                  flush=True)

    p = os.path.join(OUT, "rule_validation.csv")
    with open(p, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"[write] {p} n={len(rows)}")

    # ---- per-rule discrimination
    byrule = {}
    for r in rows:
        for rid in r["expected_rules"].split(";"):
            if not rid:
                continue
            d = byrule.setdefault(rid, dict(rule=rid, vuln_n=0, vuln_hit=0,
                                            guard_n=0, guard_fp=0))
            if r["variant"] == "vulnerable":
                d["vuln_n"] += 1
                if rid in r["reported_rules"].split(";"):
                    d["vuln_hit"] += 1
            else:
                d["guard_n"] += 1
                if rid in r["reported_rules"].split(";"):
                    d["guard_fp"] += 1
    summ = []
    for rid, d in sorted(byrule.items()):
        meta = next((x for x in R.RULES if x["id"] == rid), {})
        summ.append(dict(
            rule=rid, family=meta.get("family", ""), cwe=meta.get("cwe", ""),
            severity=meta.get("severity", ""),
            vulnerable_cases=d["vuln_n"], detected=d["vuln_hit"],
            sensitivity=round(d["vuln_hit"] / d["vuln_n"], 3) if d["vuln_n"] else "",
            guarded_cases=d["guard_n"], false_positives=d["guard_fp"],
            specificity=round(1 - d["guard_fp"] / d["guard_n"], 3) if d["guard_n"] else "",
        ))
    p2 = os.path.join(OUT, "rule_validation_summary.csv")
    with open(p2, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(summ[0].keys()))
        w.writeheader()
        w.writerows(summ)
    print(f"[write] {p2}")
    for s in summ:
        print(f"  {s['rule']}: sens={s['sensitivity']} spec={s['specificity']} "
              f"({s['detected']}/{s['vulnerable_cases']}, "
              f"fp={s['false_positives']}/{s['guarded_cases']})")
    print("VALIDATION COMPLETE")


if __name__ == "__main__":
    main()
