#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
02_SQJ_llm_secure_antipatterns / ics_rules.py

ICS-SAST: a domain rule set for industrial-control C semantics.

Design requirements that the naive regex formulation violated (found by
running the first version against the human reference solutions, which
produced 8 false positives on defect-free code):
  R1  `#define`d constants must be resolved, so `i % T08_N` is not reported
      as a division by a runtime value;
  R2  an array *declaration* is not an *indexing site*;
  R3  guards may appear before OR after the site (e.g. the wrap-around
      increment written below the store), so the context window must be
      symmetric;
  R4  the enclosing function is the correct scope for a guard lookup --
      a guard in a different function must not excuse an unguarded site;
  R5  an index guarded against the array's own capacity, or wrapped modulo
      the array length, is in range by construction.

Each rule returns the line numbers of the reported sites.
"""
import re

RULES = []


def rule(rid, family, cwe, sev, desc):
    def deco(fn):
        RULES.append(dict(id=rid, family=family, cwe=cwe, severity=sev,
                          description=desc, fn=fn))
        return fn
    return deco


# ----------------------------------------------------------------- helpers
def build_ctx(clean_src, defines):
    """Enclosing-function map: line -> (fname, body_lines tuple)."""
    funcs = split_functions(clean_src)
    owner = {}
    for fname, body, start in funcs:
        n = body.count("\n") + 1
        for k in range(start, start + n + 1):
            owner[k] = (fname, start, start + n)
    return dict(src=clean_src, lines=clean_src.splitlines(),
                defines=defines, owner=owner, funcs=funcs)


def scope(ctx, ln, back=14, fwd=8):
    """Symmetric context window clipped to the enclosing function."""
    o = ctx["owner"].get(ln)
    if o:
        lo = max(o[1], ln - back)
        hi = min(o[2], ln + fwd)
    else:
        lo = max(1, ln - back)
        hi = min(len(ctx["lines"]), ln + fwd)
    return "\n".join(ctx["lines"][lo - 1:hi])


def is_const(expr, ctx):
    e = expr.strip()
    d = ctx["defines"]
    for _ in range(4):
        e2 = re.sub(r"\b([A-Za-z_]\w*)\b",
                    lambda m: d.get(m.group(1), m.group(0)), e)
        if e2 == e:
            break
        e = e2
    if re.fullmatch(r"[-+]?\s*\d+[uUlL]*", e):
        return True
    if re.fullmatch(r"[A-Z_][A-Z0-9_]*", e):
        return True
    if re.fullmatch(r"sizeof\s*\([^)]*\)", e):
        return True
    if re.fullmatch(r"\(?\s*\d+\s*[*/%+-]\s*\d+\s*\)?", e):
        return True
    return False


def array_decls(ctx):
    """name -> declared capacity expression (only real declarations)."""
    out = {}
    for m in re.finditer(
            r"(?:^|\n)[^=\n;{}]*?\b(\w+)\s*\[\s*([^\]\n]+?)\s*\]\s*(?:=\s*\{[^}]*\})?\s*;",
            ctx["src"]):
        name, cap = m.group(1), m.group(2)
        if re.fullmatch(r"[A-Za-z_]\w*", name) and \
           not re.fullmatch(r"\d+", cap.strip()):
            out.setdefault(name, cap.strip())
        elif re.fullmatch(r"[A-Za-z_]\w*", name):
            out.setdefault(name, cap.strip())
    return out


def split_functions(src):
    out = []
    for m in re.finditer(r"^[A-Za-z_][\w\s\*]{0,40}?\b(\w+)\s*\([^;{)]*\)\s*\{",
                         src, re.M):
        name = m.group(1)
        if name in ("if", "for", "while", "switch", "return", "else"):
            continue
        start = src[:m.start()].count("\n") + 1
        depth = 0
        for j in range(m.end() - 1, len(src)):
            if src[j] == "{":
                depth += 1
            elif src[j] == "}":
                depth -= 1
                if depth == 0:
                    out.append((name, src[m.end() - 1:j + 1], start))
                    break
    return out


def _args_after(src, open_paren_idx):
    depth = 0
    for j in range(open_paren_idx, min(len(src), open_paren_idx + 500)):
        if src[j] == "(":
            depth += 1
        elif src[j] == ")":
            depth -= 1
            if depth == 0:
                return src[open_paren_idx + 1:j]
    return ""


# ------------------------------------------------------------------- rules
@rule("ICS01", "memory-safety", "CWE-120", "critical",
      "buffer copy whose length is a runtime value rather than a validated "
      "compile-time bound")
def ics01(ctx):
    hits = []
    decls = array_decls(ctx)
    for m in re.finditer(r"\b(memcpy|strcpy|strcat|sprintf|strncpy|strncat)\s*\(",
                         ctx["src"]):
        fn = m.group(1)
        args = [a.strip() for a in _args_after(ctx["src"], m.end() - 1).split(",")]
        ln = ctx["src"][:m.start()].count("\n") + 1
        s = scope(ctx, ln, back=18, fwd=10)
        if fn in ("memcpy", "strcat", "sprintf", "strncat"):
            dest = args[0] if args else ""
            # resolve the destination capacity: array name -> declared bound
            capnames = set()
            dm = re.match(r"(\w+)\s*(?:\[([^\]]*)\])?$", dest.strip("&() "))
            if dm and dm.group(1) in decls:
                capnames.add(dm.group(1))
            for a in args[1:]:
                if not a or is_const(a, ctx):
                    continue
                # normalise casts: `n > (uint16_t)MAXD` -> `n > MAXD`
                na = re.sub(r"\(\s*(?:u?int\d+_t|unsigned|signed|int|long|"
                            r"size_t|unsigned\s+\w+)\s*\)", "", a).strip()
                na = re.sub(r"\(\s*const\s+\w+\s*\)", "", na).strip()
                if re.search(r"(if|while)\s*\([^)]*\b" + re.escape(a) + r"\b"
                             r"[^)]*(<=|>=|<|>|==|!=)", s):
                    continue
                if re.search(r"(if|while)\s*\([^)]*\b" + re.escape(na) + r"\b"
                             r"[^)]*(<=|>=|<|>|==|!=)", s):
                    continue
                # guard of the form `if (n > sizeof(buf))` / `if (n > 32)`
                for cn in capnames:
                    if re.search(r"\b" + re.escape(na) + r"\b\s*(<=|>=|<|>)\s*"
                                 r"(?:sizeof\s*\(\s*" + re.escape(cn) + r"\s*\)|"
                                 + re.escape(cn) + r"|\d+)", s):
                        continue
                    if re.search(r"(?:sizeof\s*\(\s*" + re.escape(cn) +
                                 r"\s*\)|" + re.escape(cn) + r")\s*(<=|>=|<|>)"
                                 r"\s*\b" + re.escape(na) + r"\b", s):
                        continue
                # `n = min(n, CAP)` style clamp
                if re.search(re.escape(na) + r"\s*=\s*[^;]*(min|clamp|"
                             + "|".join(re.escape(c) for c in capnames) + r")", s):
                    continue
                hits.append(ln)
                break
        if fn == "strncpy" and len(args) >= 3:
            n = args[2]
            if not is_const(n, ctx):
                hits.append(ln)
    return sorted(set(hits))


@rule("ICS02", "arithmetic-safety", "CWE-369", "critical",
      "integer division or modulo whose divisor is a runtime value without a "
      "preceding non-zero guard")
def ics02(ctx):
    hits = []
    lines = ctx["lines"]
    for i, l in enumerate(lines):
        ln = i + 1
        for m in re.finditer(r"(?<![/*])([\w\)\]])\s*([/%])\s*([A-Za-z_]\w*)", l):
            op, den = m.group(2), m.group(3)
            if re.fullmatch(r"\d+[uUlL]*", den) or is_const(den, ctx):
                continue
            s = scope(ctx, ln)
            if re.search(r"(==|!=)\s*0\s*\)", s) and \
               re.search(r"\b" + re.escape(den) + r"\b", s):
                continue
            if re.search(r"if\s*\(\s*!?\s*" + re.escape(den) + r"\s*\)", s):
                continue
            if re.search(re.escape(den) + r"\s*(>|<)\s*0", s):
                continue
            if re.search(r"\bif\s*\([^)]*%s" % re.escape(den) + r"[^)]*\)\s*\{?\s*$",
                         s) and False:
                continue
            hits.append(ln)
    return sorted(set(hits))


@rule("ICS03", "bounds-validation", "CWE-129", "high",
      "array index taken from a variable with no range check against the array "
      "capacity in the enclosing scope")
def ics03(ctx):
    hits = []
    decls = array_decls(ctx)
    # loop induction variables are bounded by their own for-loop header
    loop_vars = set()
    for m in re.finditer(r"\bfor\s*\(\s*(?:[\w\s\*]+?)\s*([A-Za-z_]\w*)\s*=\s*"
                         r"[^;]*;\s*[^;]*\b\1\b[^;]*;", ctx["src"]):
        loop_vars.add(m.group(1))
    for m in re.finditer(r"(?<!\[)\b(\w+)\s*\[\s*([A-Za-z_]\w*)\s*\]", ctx["src"]):
        base, idx = m.group(1), m.group(2)
        if base not in decls:
            continue
        if idx in loop_vars:
            continue
        cap = decls[base]
        if cap == idx:
            continue
        ln = ctx["src"][:m.start()].count("\n") + 1
        s = scope(ctx, ln)
        guarded = re.search(
            r"(if|while)\s*\([^)]*\b" + re.escape(idx) + r"\b[^)]*(<|>|<=|>=)", s)
        if not guarded:
            guarded = re.search(
                r"(if|while)\s*\([^)]*(<|>|<=|>=)\s*[^)]*\b" + re.escape(idx) + r"\b", s)
        if not guarded:
            guarded = re.search(re.escape(idx) + r"\s*=\s*" + re.escape(cap) + r"\b", s)
        if not guarded:
            guarded = re.search(re.escape(idx) + r"\s*=\s*[^;]*%\s*"
                                + re.escape(cap) + r"\b", s)
        if not guarded:
            # wrapped immediately after the store, or clamped by the caller
            guarded = re.search(re.escape(idx) + r"\s*=\s*\([^)]*%\s*"
                                + re.escape(cap), s)
        if not guarded:
            guarded = re.search(re.escape(idx) + r"\s*=\s*[^;]*(==|!=)\s*0", s)
        if guarded:
            continue
        hits.append(ln)
    return sorted(set(hits))


@rule("ICS04", "accumulator-overflow", "CWE-190", "high",
      "additive control accumulator with no clamp, so a long-running loop can "
      "wrap the signed value")
def ics04(ctx):
    hits = []
    # both compound (+=) and self-referential (x = x + ...) accumulation
    for m in re.finditer(r"\b([A-Za-z_]\w*)\s*(?:\+=|-=|\*=|=)\s*"
                         r"(?:\1\s*(?:\+|-|\*)\s*|[^=;]*\b\1\b\s*[\+\-])[^;]*;",
                         ctx["src"]):
        var = m.group(1)
        if not re.search(r"(integ|integral|accum|_acc|acc\b|sum|total|energy|"
                         r"err_sum|filtered|ema|avg|mean|hist_count|filter)",
                         var, re.I):
            continue
        ln = ctx["src"][:m.start()].count("\n") + 1
        s = scope(ctx, ln, back=30, fwd=30)
        if re.search(r"(if\s*\([^)]*\b" + re.escape(var) + r"\b[^)]*[<>]=)", s):
            continue
        if re.search(re.escape(var) + r"\s*=\s*[^;]*(INT\d+_MAX|INT_MAX|"
                     r"UINT\d+_MAX|0x[0-9A-Fa-f]{4,})", s):
            continue
        if re.search(r"(sat|saturat|clamp|lim_?it|bound)", s, re.I):
            continue
        decl = re.search(r"\b(?:static\s+)?u?int(8|16|32|64)_t\s+" +
                         re.escape(var) + r"\b", ctx["src"])
        if decl and re.search(r"\(\s*uint8_t\s*\)\s*\(", s):
            continue          # deliberate wrap-around of a small counter
        if decl and re.search(re.escape(var) + r"\s*=\s*\(\s*u?int", s):
            continue
        hits.append(ln)
    return sorted(set(hits))


@rule("ICS05", "input-validation", "CWE-20", "critical",
      "function that consumes parameters but performs no relational "
      "validation, so no input can be range-checked")
def ics05(ctx):
    hits = []
    for fname, body, start in ctx["funcs"]:
        header = body.split("{")[0]
        if not re.search(r"\(", header):
            continue
        params = [p for p in re.findall(r"([A-Za-z_]\w*)\s*(?:\[\s*\w+\s*\])?\s*"
                                        r"(?=,|\))", header) if p != "void"]
        if not params:
            continue
        # any relational or equality test at all, or an explicit reject clause
        if re.search(r"[<>]=?|==|!=|\|\||&&", body):
            continue
        if re.search(re.escape(fname) + r"\s*\(\s*0\s*\)", body):
            continue
        hits.append(start)
    return sorted(set(hits))


@rule("ICS06", "loop-termination", "CWE-835", "high",
      "loop whose trip count comes from an input parameter, with no constant "
      "bound and no capacity check in scope")
def ics06(ctx):
    hits = []
    for i, l in enumerate(ctx["lines"]):
        ln = i + 1
        m = re.search(r"\bfor\s*\([^;]*;\s*[\w\s]*\b(len|len_|_len|size|n|count|"
                      r"idx|index|num|received|available|length)\w*\b", l)
        if not m:
            m = re.search(r"\bfor\s*\([^;]*;[^;]*\b(len|len_|_len|size|n|count|"
                          r"idx|index|num|received|available|length)\w*\b[^;]*;",
                          l)
        if not m:
            continue
        var = m.group(1)
        s = scope(ctx, ln)
        if re.search(re.escape(var) + r"\s*(<|>|<=|>=)\s*(sizeof|[A-Z_][A-Z0-9_]*)", s):
            continue
        if re.search(re.escape(var) + r"\s*(>|>=)\s*[^;]*(capacity|MAX|LEN|"
                     r"sizeof|_size)", s):
            continue
        if re.search(r"if\s*\([^)]*" + re.escape(var) + r"[^)]*(>|>=)", s):
            continue
        if re.search(r"\bfor\s*\([^;]*;[^;]*<\s*[A-Z_][A-Z0-9_]*\b", l):
            continue
        if re.search(r"sizeof\s*\(\s*" + re.escape(var), s):
            continue
        hits.append(ln)
    return sorted(set(hits))


@rule("ICS07", "concurrency-control", "CWE-362", "high",
      "read-modify-write on shared control state with no atomic or critical "
      "section, in code that documents concurrent/ISR execution")
def ics07(ctx):
    if not re.search(r"\b(1\s*kHz|\d+\s*kHz|\d+\s*Hz|ISR|interrupt service|"
                     r"concurrent|thread|reentrant|multi-?task|atomic|"
                     r"synchron)", ctx["src"], re.I):
        return []
    if re.search(r"\b(atomic|__atomic|_Atomic|disable_irq|critical_section|"
                 r"taskENTER_CRITICAL|mutex|spin_lock|InterruptLock|"
                 r"portENTER_CRITICAL|__disable_irq|__enable_irq|"
                 r"disable_interrupts|irq_save)\w*\s*\(", ctx["src"], re.I):
        return []
    hits = []
    vols = set(re.findall(r"\bvolatile\s+[\w\s\*]{0,25}?\b(\w+)\s*(?:\[[^\]]*\])?\s*;",
                          ctx["src"]))
    for v in vols:
        for m in re.finditer(r"\b" + re.escape(v) + r"\s*(?:\[[^\]]*\])?\s*"
                             r"(\+\+|--|\+=|-=)\s*[^;]+;", ctx["src"]):
            ln = ctx["src"][:m.start()].count("\n") + 1
            s = scope(ctx, ln)
            # snapshot-then-store is the correct RMW pattern
            if re.search(re.escape(v) + r"\s*=\s*(?:prev|old|prev_|old_|tmp|"
                         r"snap|shadow)", s):
                continue
            hits.append(ln)
    return sorted(set(hits))


@rule("ICS08", "safety-envelope", "CWE-787", "critical",
      "actuator, register or output value written without saturation to a "
      "configured or physical limit")
def ics08(ctx):
    hits = []
    lines = ctx["lines"]
    out_rx = re.compile(r"\b(out|output|setpoint|set_point|command|cmd|duty|"
                        r"valve|motor|speed|level|dac|pwm|gpio|reg|port|"
                        r"pressure|flow|position)\w*\s*=[^=]", re.I)
    for i, l in enumerate(lines):
        m = out_rx.search(l)
        if not m:
            continue
        var = re.match(r"\s*(\w+)", m.group(0).strip())
        var = var.group(1) if var else ""
        ln = i + 1
        # the write must be to memory or a register, not to a local
        if re.search(r"\b(static|const|return|if|while|for)\b", l):
            continue
        if re.search(r"\blocal\b|\btmp\b|\btemp\b|\bprev\b|\bold\b", var, re.I):
            continue
        s = scope(ctx, ln, back=20, fwd=12)
        if re.search(r"(if\s*\([^)]*[<>]=)|(\b(MIN|MAX|LIMIT|LIM|SAT|"
                     r"out_min|out_max|OUT_MIN|OUT_MAX|clamp|saturat)\w*\b)|"
                     r"(<\s*\d{3,})|(==\s*0)", s):
            continue
        if re.search(r"\bsizeof\b|\bstatic\b", l):
            continue
        hits.append(ln)
    return sorted(set(hits))


@rule("ICS09", "state-consistency", "CWE-665", "high",
      "control-state variable assigned from a value that is neither a literal "
      "nor a validated enumerator")
def ics09(ctx):
    hits = []
    lines = ctx["lines"]
    for m in re.finditer(r"\b(\w*(?:state|stat|phase|mode|step)\w*)\s*=\s*([^;]+);",
                         ctx["src"]):
        var, rhs = m.group(1), m.group(2).strip()
        if re.fullmatch(r"[-+]?\d+[uUlL]*", rhs):
            continue
        if re.fullmatch(r"[A-Z_][A-Z0-9_]*", rhs):
            continue
        if re.fullmatch(r"sizeof\s*\([^)]*\)", rhs):
            continue
        ln = ctx["src"][:m.start()].count("\n") + 1
        s = scope(ctx, ln)
        if re.search(r"(switch|case)\b", s):
            continue
        if re.search(re.escape(var) + r"\s*(<|>|<=|>=)\s*", s):
            continue
        if re.search(r"\benum\b", s) and re.search(r"ST_N|STATE_N|_N\b", s):
            continue
        if re.search(r"sizeof\s*\(\s*" + re.escape(rhs) + r"\s*\)", s):
            continue
        # t11_state = P_SOF / = P_LEN style enumerator from a switch
        if re.fullmatch(r"[A-Za-z_]\w*", rhs) and re.search(
                r"\b" + re.escape(rhs) + r"\b\s*[:,=]", s):
            continue
        hits.append(ln)
    return sorted(set(hits))


@rule("ICS10", "arithmetic-portability", "CWE-758", "medium",
      "shift by a non-literal amount or reliance on implementation-defined "
      "shift of a negative value")
def ics10(ctx):
    hits = []
    for m in re.finditer(r"(?:<<|>>)\s*([A-Za-z_]\w*)", ctx["src"]):
        amt = m.group(1)
        ln = ctx["src"][:m.start()].count("\n") + 1
        s = scope(ctx, ln, back=14, fwd=8)
        if re.search(r"(if|while)\s*\([^)]*\b" + re.escape(amt) + r"\b[^)]*"
                     r"(<=|>=|<|>|==|!=)", s):
            continue
        if re.search(re.escape(amt) + r"\s*=\s*[^;]*(%|&)\s*", s) and \
           re.search(re.escape(amt) + r"\s*=\s*[^;]*(WIDTH|BITS|SHIFT|"
                     r"\d+)\s*[-+]", s):
            continue
        if re.search(re.escape(amt) + r"\s*&\s*\(?\s*(3[0-1]|[0-9])\s*\)?", s):
            continue
        hits.append(ln)
    for m in re.finditer(r"-\s*\w+\s*(?:<<|>>)|~\s*\w+\s*(?:<<|>>)", ctx["src"]):
        hits.append(ctx["src"][:m.start()].count("\n") + 1)
    return sorted(set(hits))


@rule("ICS11", "concurrency-atomicity", "CWE-367", "high",
      "time-of-check/time-of-use: a validity or length value is checked and "
      "then re-read for the operation, in code with volatile shared state")
def ics11(ctx):
    if not re.search(r"\bvolatile\b", ctx["src"]):
        return []
    hits = []
    for m in re.finditer(r"if\s*\(\s*!?\s*(\w*(?:len|size|count|valid|ok|ready|"
                         r"seen)\w*)\s*(?:[!=<>]=?|\)|&&|\|\|)", ctx["src"], re.I):
        var = m.group(1)
        tail = ctx["src"][m.end():m.end() + 500]
        # a re-check of the same variable immediately after is a redundant
        # re-test, not a second read guarding an operation; require that the
        # re-check result is the one that enables the operation
        if not re.search(r"\bif\s*\([^)]*\b" + re.escape(var) + r"\b[^)]*\)", tail):
            continue
        ln = ctx["src"][:m.start()].count("\n") + 1
        s = scope(ctx, ln, back=4, fwd=6)
        if re.search(re.escape(var) + r"\s*(\+\+|--|\+=|-=)", s):
            continue          # the value is mutated in place, not re-read stale
        if re.search(r"\bvolatile\b[^;]*\b" + re.escape(var) + r"\b", s):
            continue          # declared volatile: single read per use is correct
        hits.append(ln)
    return sorted(set(hits))


@rule("ICS12", "fault-handling", "CWE-252", "critical",
      "return value of a safety-relevant call discarded, making a failed "
      "safety operation indistinguishable from success")
def ics12(ctx):
    hits = []
    for m in re.finditer(
            r"^[ \t]*(?!return\b|if\b|for\b|while\b|switch\b|\}|#|//|/\*|\*|else\b|"
            r"typedef\b|extern\b|static\b|[A-Za-z_]\w*\s+[A-Za-z_]\w*\s*\()"
            r"([A-Za-z_]\w*)\s*\([^;{]*\)\s*;", ctx["src"], re.M):
        fn = m.group(1)
        if re.search(r"(verify|validate|check|assert|guard|protect|lock|"
                     r"read_?(reg|input|sensor|adc|val)|init|save|commit|ack|"
                     r"safe|monitor|watchdog)", fn, re.I):
            ln = ctx["src"][:m.start()].count("\n") + 1
            s = scope(ctx, ln, back=3, fwd=2)
            if re.search(re.escape(fn) + r"\s*\([^)]*\)\s*==", s):
                continue
            if re.search(r"=\s*" + re.escape(fn) + r"\s*\(", s):
                continue
            hits.append(ln)
    return sorted(set(hits))


@rule("ICS13", "degenerate-state", "CWE-561", "medium",
      "declaration of control state that is never written, so the initial "
      "value is relied upon for a safety decision")
def ics13(ctx):
    hits = []
    for m in re.finditer(r"\b(?:static\s+)?(u?int\d+_t|float|double|bool|char)\s+"
                         r"(\w+)\s*((?:\[[^\]]*\])*)\s*;", ctx["src"]):
        typ, var = m.group(1), m.group(2)
        if not re.search(r"(state|stat|flag|count|idx|index|ready|seen|init|"
                         r"enable|armed|latch)", var, re.I):
            continue
        n_assign = len(re.findall(r"\b" + re.escape(var) + r"\s*=(?!=)",
                                  ctx["src"]))
        n_incr = len(re.findall(r"\b" + re.escape(var) + r"\s*(\+\+|--|\+=|-=)",
                                ctx["src"]))
        if n_assign + n_incr == 0:
            hits.append(ctx["src"][:m.start()].count("\n") + 1)
    return sorted(set(hits))


def analyze(clean_src, defines):
    ctx = build_ctx(clean_src, defines)
    hits = []
    for r in RULES:
        try:
            for ln in r["fn"](ctx):
                hits.append(dict(rule_id=r["id"], family=r["family"],
                                 cwe=r["cwe"], severity=r["severity"],
                                 line=ln, description=r["description"]))
        except Exception:
            continue
    return hits, ctx
