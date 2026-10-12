"""Print today's feed for a user: uv run python scripts/show_feed.py reema_v1"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from feed.embed import embed
from feed.pipeline import EMBED_MODEL, build_feed
from feed.schemas import Profile, Tip

EXTRACTIONS = ROOT / "data" / "extraction_results_claude-haiku-5.5.json"


def load(name: str):
    library = [Tip(**t) for t in json.loads((ROOT / "data" / "library.json").read_text())]
    vecs = embed([t.canonical_description for t in library], EMBED_MODEL)
    prof = next(Profile(**r["profile"]) for r in json.loads(EXTRACTIONS.read_text()) if r["pep"] == name)
    return library, vecs, prof


if __name__ == "__main__":
    name = sys.argv[1] if len(sys.argv) > 1 else "reema_v1"
    library, vecs, prof = load(name)
    feed, excluded = build_feed(prof, library, vecs)
    titles = {t.tip_id: next(v.title for v in t.variants if v.language == "en") if any(v.language == "en" for v in t.variants) else t.variants[0].title for t in library}
    print(f"\n=== {name}: today's feed (language {prof.language}) ===")
    for n, f in enumerate(feed, 1):
        print(f"{n:2}. [{f.slot:12}] {titles[f.tip_id][:48]:48} ({f.language}){' 🔒discreet' if f.discreet else ''}  ← {f.reason}")
    print(f"\nexcluded by safety filter: {len(excluded)}")
    for tid, why in list(excluded.items())[:12]:
        print(f"   ✗ {titles[tid][:48]:48} {why}")
