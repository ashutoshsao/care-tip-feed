"""Prototype step 4: compare extraction models on the hand-labeled profiles.

Scores each model raw (LLM only) and after the D7 checks (code → verifier → safer status).
"""

import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from feed.extract import code_checks, extract, verify
from feed.llm import PRICES, USAGE, cost

MODELS = ["anthropic/claude-haiku-5.5", "deepseek/deepseek-v4.1-flash", "google/gemini-3.8-flash"]
VERIFIER = {"anthropic": "google/gemini-3.8-flash", "deepseek": "anthropic/claude-haiku-5.5",
            "google": "anthropic/claude-haiku-5.5"}   # different family from the extractor
PEPS = ["reema_v1", "reema_v2", "arjun", "priya", "ramesh", "neha"]
GOLD = json.loads((ROOT / "data" / "gold.json").read_text())


def score(name, prof):
    g = GOLD[name]
    crit, crit_total = [], 0
    active = {r.code for r in prof.red_flags if r.status == "active"}
    confirmed = {i.code for i in prof.issues if i.status == "confirmed"}
    present = {i.code for i in prof.issues}
    tests = {t.code: t.status for t in prof.tests}

    def check(ok, msg):
        nonlocal crit_total
        crit_total += 1
        if not ok:
            crit.append(msg)

    for c in g.get("must_red_flags_active", []):
        check(c in active, f"missed active red flag {c}")
    for c in g.get("must_not_red_flags_active", []):
        check(c not in active, f"false/uncleared red flag {c}")
    for c in g.get("must_confirmed", []):
        check(c in confirmed, f"{c} should be confirmed")
    for c in g.get("must_not_confirmed", []):
        check(c not in confirmed, f"{c} wrongly confirmed")
    for c in g.get("must_not_present", []):
        check(c not in present, f"{c} wrongly attributed (family/negated)")
    for c, ok_statuses in g.get("must_tests", {}).items():
        check(tests.get(c) in ok_statuses, f"test {c}: got {tests.get(c)}, want {ok_statuses}")
    if "must_restrictions" in g:
        for c in g["must_restrictions"]:
            check(c in {r.code for r in prof.restrictions}, f"missed restriction {c}")
    check((prof.life_stage == "pregnant") == g["must_pregnant"], "pregnancy wrong")
    check(prof.language == g["language"], f"language {prof.language} != {g['language']}")

    def recall(exp, got):
        return (len(set(exp) & got), len(exp))

    ri = recall(g["expect_issues"], present)
    rv = recall(g["expect_interventions"], {x.code for x in prof.interventions})
    return {"critical_errors": crit, "critical_checks": crit_total, "issue_recall": ri, "intervention_recall": rv}


def run_one(model, name):
    pep = (ROOT / "data" / "peps" / f"{name}.xml").read_text()
    prev = None
    raw = extract(pep, model)
    if name == "reema_v2":   # diff against the previous version (D11)
        prev = extract((ROOT / "data" / "peps" / "reema_v1.xml").read_text(), model)
    flags = code_checks(pep, raw, prev)
    fixed, unresolved = verify(pep, raw, flags, VERIFIER[model.split("/")[0]])
    return model, name, raw, flags, fixed, unresolved


def main(models=MODELS, runs: int = 2):
    jobs = [(m, n) for m in models for n in PEPS for _ in range(runs)]
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda j: run_one(*j), jobs))
    out, summary = [], {}
    for model, name, raw, flags, fixed, unresolved in results:
        s_raw, s_fix = score(name, raw), score(name, fixed)
        out.append({"model": model, "pep": name, "flags": flags, "unresolved": unresolved,
                    "raw": s_raw, "after_checks": s_fix, "profile": fixed.model_dump()})
        agg = summary.setdefault(model, {"raw_crit": 0, "fix_crit": 0, "checks": 0, "flags": 0,
                                         "iss": [0, 0], "int": [0, 0]})
        agg["raw_crit"] += len(s_raw["critical_errors"])
        agg["fix_crit"] += len(s_fix["critical_errors"])
        agg["checks"] += s_raw["critical_checks"]
        agg["flags"] += len(flags)
        for k, key in (("iss", "issue_recall"), ("int", "intervention_recall")):
            agg[k][0] += s_fix[key][0]
            agg[k][1] += s_fix[key][1]
    (ROOT / "data" / "extraction_results.json").write_text(json.dumps(out, indent=1, default=str))
    print(f"{'model':32} {'crit raw':>9} {'crit after':>11} {'flags':>6} {'issue rec':>10} {'interv rec':>11} {'$/extract':>10}")
    for m, a in summary.items():
        per = cost(m) / max(USAGE.get(m, {}).get("calls", 1), 1)
        print(f"{m:32} {a['raw_crit']:>4}/{a['checks']:<4} {a['fix_crit']:>6}/{a['checks']:<4} {a['flags']:>6} "
              f"{a['iss'][0]/a['iss'][1]:>10.0%} {a['int'][0]/a['int'][1]:>11.0%} {per:>10.5f}")
    print("total spend $", round(sum(cost(m) for m in USAGE), 3))


if __name__ == "__main__":
    main(sys.argv[1:] or MODELS)
