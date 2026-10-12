"""Cross-check the hand-written gold labels with two independent non-Claude annotators.

The gold was written by Claude (this session); scoring Claude-family extractors against it could be biased.
Each annotator answers the same questions blind; disagreements go to the human to decide.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from feed import vocab
from feed.llm import USAGE, chat_json, cost

ANNOTATORS = ["google/gemini-3.1-pro-preview", "openai/gpt-6.1-sol"]
PEPS = ["reema_v1", "reema_v2", "arjun", "priya", "ramesh", "neha"]
GOLD = json.loads((ROOT / "data" / "gold.json").read_text())

SYSTEM = """You are a careful clinical annotator. Read the patient profile and answer strictly from what it says.
- red_flags_active: urgent concerns reported and NOT yet medically cleared.
- conditions_confirmed: diagnosed or clearly established for THIS person (not family history, not negated,
  not merely suspected or awaiting tests).
- tests: each test mentioned and its current stage (advised/scheduled/sample_collected/results_received).
- explicit_restrictions: only restrictions a clinician explicitly advised.
- pregnant, language."""

SCHEMA = {"type": "object", "additionalProperties": False,
          "required": ["red_flags_active", "conditions_confirmed", "tests", "explicit_restrictions",
                       "pregnant", "language"],
          "properties": {
              "red_flags_active": {"type": "array", "items": {"type": "string", "enum": vocab.RED_FLAGS}},
              "conditions_confirmed": {"type": "array", "items": {"type": "string", "enum": vocab.ISSUES}},
              "tests": {"type": "array", "items": {"type": "object", "additionalProperties": False,
                        "required": ["code", "status"],
                        "properties": {"code": {"type": "string", "enum": vocab.TESTS},
                                       "status": {"type": "string", "enum": vocab.TEST_STATUS}}}},
              "explicit_restrictions": {"type": "array", "items": {"type": "string", "enum": vocab.RESTRICTIONS}},
              "pregnant": {"type": "boolean"},
              "language": {"type": "string", "enum": vocab.LANGUAGES}}}


def disagreements(name, a):
    g, out = GOLD[name], []
    active = set(a["red_flags_active"])
    if set(g.get("must_red_flags_active", [])) - active:
        out.append(f"red flag missing: {set(g['must_red_flags_active']) - active}")
    if active & set(g.get("must_not_red_flags_active", [])):
        out.append(f"red flag active, gold says not: {active & set(g['must_not_red_flags_active'])}")
    conf = set(a["conditions_confirmed"])
    if set(g.get("must_confirmed", [])) - conf:
        out.append(f"not confirmed, gold says confirmed: {set(g['must_confirmed']) - conf}")
    if conf & set(g.get("must_not_confirmed", [])):
        out.append(f"confirmed, gold says not: {conf & set(g['must_not_confirmed'])}")
    tests = {t["code"]: t["status"] for t in a["tests"]}
    for code, ok in g.get("must_tests", {}).items():
        if tests.get(code) not in ok:
            out.append(f"test {code}: annotator {tests.get(code)}, gold {ok}")
    want = set(g.get("must_restrictions", []))
    got = set(a["explicit_restrictions"])
    accepted = [set(x) for x in g.get("accept_restrictions", [])]
    if accepted and got not in accepted or not accepted and got != want:
        out.append(f"restrictions: annotator {sorted(got)}, gold {sorted(want) or accepted}")
    if a["pregnant"] != g["must_pregnant"]:
        out.append(f"pregnant: annotator {a['pregnant']}, gold {g['must_pregnant']}")
    if a["language"] != g["language"]:
        out.append(f"language: annotator {a['language']}, gold {g['language']}")
    return out


def main():
    report = {}
    for model in ANNOTATORS:
        for name in PEPS:
            pep = (ROOT / "data" / "peps" / f"{name}.xml").read_text()
            ans = chat_json(model, SYSTEM, f"<profile>\n{pep}\n</profile>", SCHEMA, name="annotation")
            report.setdefault(name, {})[model] = {"answer": ans, "disagreements": disagreements(name, ans)}
    (ROOT / "data" / "gold_crosscheck.json").write_text(json.dumps(report, indent=1))
    for name, by_model in report.items():
        for model, r in by_model.items():
            print(f"{name:9} {model:32} {'agrees' if not r['disagreements'] else r['disagreements']}")
    print("spend $", round(sum(cost(m) for m in USAGE), 3))


if __name__ == "__main__":
    main()
