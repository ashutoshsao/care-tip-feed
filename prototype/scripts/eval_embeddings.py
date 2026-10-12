"""Compare embedding models: English profile phrases → Hindi tip videos (cross-lingual) vs English tips."""

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from feed import vocab
from feed.embed import embed
from feed.schemas import Tip

MODELS = ["qwen3-embedding:0.6b", "bge-m3"]
# Real phrases from the test profiles → the issue code they should find.
QUERIES = [
    ("severe menstrual pain", "menstrual_pain"),
    ("cycle length varies, sometimes 8 days off", "cycle_irregularity"),
    ("erratic sleep cycle due to night shifts", "shift_work_sleep"),
    ("difficulty sleeping during day", "insomnia"),
    ("chronic lower back pain", "lower_back_pain"),
    ("leg swelling (worse at night)", "leg_swelling"),
    ("Vaginal laxity (post-delivery)", "vaginal_laxity"),
    ("Right knee pain after running", "knee_pain"),
    ("occasional acid reflux after late dinners", "acid_reflux"),
    ("morning nausea, improving", "pregnancy_nausea"),
    ("mild constipation", "constipation"),
    ("Type 2 diabetes diagnosed 3 years ago", "type2_diabetes"),
    ("high blood pressure on medication", "hypertension"),
    ("Feels stressed at work", "stress"),
    ("Anxious about pregnancy", "anxiety"),
    ("fatigue; lethargy", "fatigue"),
]


def score(q_vecs, t_vecs, relevant, k=5):
    hits, rr = 0, 0.0
    for qv, rel in zip(q_vecs, relevant):
        order = np.argsort(-(t_vecs @ qv))
        ranks = [r for r, j in enumerate(order) if j in rel]
        hits += bool(ranks) and ranks[0] < k
        rr += 1 / (ranks[0] + 1) if ranks else 0
    sims = t_vecs @ t_vecs.T
    off = sims[np.triu_indices(len(t_vecs), 1)]
    return hits / len(q_vecs), rr / len(q_vecs), float(np.median(off)), float(np.percentile(off, 95))


def main():
    lib = [Tip(**t) for t in json.loads((ROOT / "data" / "library.json").read_text())]
    lib = [t for t in lib if any(v.language == "hi" for v in t.variants)]
    hi = [next(v for v in t.variants if v.language == "hi") for t in lib]
    hi_text = [f"{v.title}. {v.description}. {v.transcript}" for v in hi]
    en_text = [t.canonical_description for t in lib]
    relevant = [{j for j, t in enumerate(lib) if set(vocab.expand(code)) & set(t.conditions)} for _, code in QUERIES]
    print(f"{len(QUERIES)} English queries vs {len(lib)} tips (Hindi versions)\n")
    print(f"{'model':22} {'setting':22} {'hit@5':>6} {'MRR':>6} {'tip-tip sim median / p95':>26}")
    out = {}
    for m in MODELS:
        q = embed([t for t, _ in QUERIES], m)
        for setting, texts in (("English → Hindi tips", hi_text), ("English → English tips", en_text)):
            r = score(q, embed(texts, m), relevant)
            out[f"{m} | {setting}"] = r
            print(f"{m:22} {setting:22} {r[0]:>6.0%} {r[1]:>6.2f} {r[2]:>14.2f} / {r[3]:.2f}")
    (ROOT / "data" / "embedding_eval.json").write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
