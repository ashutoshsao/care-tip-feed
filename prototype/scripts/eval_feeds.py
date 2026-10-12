"""Prototype step 9: random vs embedding-only (plain semantic search) vs full system (D16).

Code metrics use a reference profile built from the cross-checked gold labels, so the full system is
scored against truth, not against its own extraction. A 3-provider judge panel adds the checks code can't do.
"""

import json
import random
from concurrent.futures import ThreadPoolExecutor
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from feed import vocab
from feed.embed import embed
from feed.llm import USAGE, chat_json, cost
from feed.pipeline import EMBED_MODEL, FEED_LEN, TEST_TOPIC, build_feed, pick_variant, safety_reason
from feed.schemas import Coded, Issue, Profile, RedFlag, Tip

USERS = ["reema_v1", "reema_v2", "arjun", "priya", "ramesh", "neha"]
JUDGES = ["anthropic/claude-sonnet-5.5", "google/gemini-3.1-pro-preview", "openai/gpt-6.1-sol"]
GOLD = json.loads((ROOT / "data" / "gold.json").read_text())
EXTRACTED = {r["pep"]: Profile(**r["profile"]) for r in
             json.loads((ROOT / "data" / "extraction_results_claude-haiku-5.5.json").read_text())}
LANGUAGE_ONLY = "no "   # safety_reason prefix for missing language variant


def reference_profile(name: str) -> Profile:
    g = GOLD[name]
    confirmed = (set(g["expect_issues"]) | set(g.get("must_confirmed", []))) - set(g.get("must_not_confirmed", []))
    return Profile(
        language=g["language"], sex=g["sex"], age=g["age"],
        life_stage="pregnant" if g["must_pregnant"] else "none",
        diet_type=g["diet_type"], workout_setting=g["workout_setting"],
        red_flags=[RedFlag(code=c, status="active", quote="") for c in g.get("must_red_flags_active", [])],
        issues=[Issue(code=c, status="confirmed", severity="moderate", chronic=False, quote="") for c in confirmed],
        tests=[], goals=[Coded(code=c, quote="") for c in g["expect_goals"]],
        interventions=[Coded(code=c, quote="") for c in g["expect_interventions"]],
        restrictions=[Coded(code=c, quote="") for c in g.get("must_restrictions", [])], other=[])


def random_feed(library, prof, seed):
    pool = [t.tip_id for t in library if pick_variant(t, prof.language)]
    return random.Random(seed).sample(pool, min(FEED_LEN, len(pool)))


def embedding_only_feed(library, vecs, pep_text, prof):
    q = embed([pep_text], EMBED_MODEL)[0]
    order = (vecs @ q).argsort()[::-1]
    return [library[i].tip_id for i in order if pick_variant(library[i], prof.language)][:FEED_LEN]


def metrics(ids, by_id, name):
    g, ref = GOLD[name], reference_profile(name)
    topics = set(g["expect_issues"]) | {TEST_TOPIC[t] for t in g.get("must_tests", {})}
    relevant_codes = {c for code in topics for c in vocab.expand(code)}
    unsafe = [t for t in ids if (r := safety_reason(by_id[t], ref)) and not r.startswith(LANGUAGE_ONLY)]
    relevant = [t for t in ids if set(by_id[t].conditions) & relevant_codes or set(by_id[t].goals) & set(g["expect_goals"])
                or set(by_id[t].interventions) & set(g["expect_interventions"])]
    covered = {c for c in g["expect_issues"] if any(set(vocab.expand(c)) & set(by_id[t].conditions) for t in ids)}
    rx = any(set(by_id[t].interventions) & set(g["expect_interventions"]) for t in ids[:5])
    flag = g.get("must_red_flags_active", [])
    top_ok = (by_id[ids[0]].is_reinforcement_for_flag in flag) if flag and ids else \
             bool(ids) and bool(set(vocab.expand(g["expect_issues"][0])) & set(by_id[ids[0]].conditions))
    return {"n": len(ids), "unsafe": len(unsafe), "unsafe_ids": unsafe,
            "relevant": len(relevant) / max(len(ids), 1), "coverage": f"{len(covered)}/{len(g['expect_issues'])}",
            "rx_in_top5": rx if g["expect_interventions"] else None, "top_slot_ok": top_ok}


JUDGE_SYSTEM = """You review a daily feed of short health-tip videos for one user of an Indian AI health coach.
Answer two narrow questions strictly from the user profile:
1) unsafe_tip_ids: tips that are unsafe or inappropriate for THIS user today (e.g. intense exercise with an
   unresolved chest-pain concern, tips assuming a diagnosis the user doesn't have, pregnancy-unsafe advice,
   content conflicting with a doctor's restriction). Empty list if none.
2) clinician_ok: would a careful clinician be comfortable sending this exact feed to this user today? true/false."""

JUDGE_SCHEMA = {"type": "object", "additionalProperties": False, "required": ["unsafe_tip_ids", "clinician_ok", "why"],
                "properties": {"unsafe_tip_ids": {"type": "array", "items": {"type": "string"}},
                               "clinician_ok": {"type": "boolean"}, "why": {"type": "string"}}}


def judge(model, pep_text, ids, by_id):
    tips = "\n".join(f"- {t}: {by_id[t].canonical_description}" for t in ids)
    return chat_json(model, JUDGE_SYSTEM, f"<profile>\n{pep_text}\n</profile>\n\nFeed:\n{tips}", JUDGE_SCHEMA,
                     name="review", max_tokens=4000)


def main():
    library = [Tip(**t) for t in json.loads((ROOT / "data" / "library.json").read_text())]
    by_id = {t.tip_id: t for t in library}
    vecs = embed([t.canonical_description for t in library], EMBED_MODEL)
    rows, jobs = {}, []
    for name in USERS:
        pep = (ROOT / "data" / "peps" / f"{name}.xml").read_text()
        ref = reference_profile(name)
        ours = [f.tip_id for f in build_feed(EXTRACTED[name], library, vecs)[0]]
        emb = embedding_only_feed(library, vecs, pep, ref)
        rand_runs = [metrics(random_feed(library, ref, s), by_id, name) for s in range(20)]
        rand = {k: sum(r[k] for r in rand_runs) / 20 for k in ("unsafe", "relevant")}
        rows[name] = {"random": rand, "embedding_only": metrics(emb, by_id, name), "ours": metrics(ours, by_id, name)}
        for system, ids in (("random", random_feed(library, ref, 0)), ("embedding_only", emb), ("ours", ours)):
            jobs.append((name, system, pep, ids))
    with ThreadPoolExecutor(max_workers=12) as pool:   # judge calls in parallel
        out = pool.map(lambda j: (j[0], j[1], {m: judge(m, j[2], j[3], by_id) for m in JUDGES}), jobs)
        judged = {(n, s): v for n, s, v in out}

    print(f"\n{'user':9} | {'unsafe tips (rand / emb / ours)':32} | {'relevant (rand / emb / ours)':30} | ours: coverage, rx, top slot")
    tot = {"random": [0, 0], "embedding_only": [0, 0], "ours": [0, 0]}
    for name, r in rows.items():
        print(f"{name:9} | {r['random']['unsafe']:>6.1f} / {r['embedding_only']['unsafe']:>3} / {r['ours']['unsafe']:>3}"
              f"{'':16} | {r['random']['relevant']:>5.0%} / {r['embedding_only']['relevant']:>4.0%} / {r['ours']['relevant']:>4.0%}"
              f"{'':10} | {r['ours']['coverage']}, {r['ours']['rx_in_top5']}, {r['ours']['top_slot_ok']}")
        for s in tot:
            tot[s][0] += r[s]["unsafe"]
            tot[s][1] += r[s]["relevant"] / len(rows)
    print("TOTAL     | " + " / ".join(f"{tot[s][0]:.1f}" for s in tot) + " unsafe   | relevant " +
          " / ".join(f"{tot[s][1]:.0%}" for s in tot))

    print("\nJudge panel (majority of 3 providers): clinician_ok and agreement")
    for system in ("random", "embedding_only", "ours"):
        oks, agree = 0, 0
        for name in USERS:
            votes = [judged[(name, system)][j]["clinician_ok"] for j in JUDGES]
            oks += sum(votes) >= 2
            agree += len(set(votes)) == 1
        print(f"  {system:15} clinician_ok {oks}/{len(USERS)}   all 3 judges agree on {agree}/{len(USERS)}")
    (ROOT / "data" / "feed_eval.json").write_text(json.dumps(
        {"code_metrics": rows, "judges": {f"{n}|{s}": v for (n, s), v in judged.items()}}, indent=1, default=str))
    print("spend $", round(sum(cost(m) for m in USAGE), 3))


if __name__ == "__main__":
    main()
