"""PEP → structured profile, then the D7 checks (code → LLM if flagged → safer status)."""

import re

from . import vocab
from .llm import chat_json, strict_schema
from .schemas import Profile

SYSTEM = """You convert a patient's health profile (XML, written by a health coach) into structured facts.
Rules:
- Use ONLY codes from the enums. Anything important with no matching code goes in `other`.
- `quote` must be copied VERBATIM from the profile (an exact substring, no paraphrase).
- Status, not just presence:
  * issues: confirmed = stated as diagnosed/confirmed or clearly ongoing symptoms; suspected = possible,
    not yet established; resolved = ruled out or no longer present. Symptoms the user clearly reports
    (pain, fatigue, poor sleep) count as confirmed. Negated items ("no X", "X ruled out") are NOT
    confirmed. A family member's condition is NOT the user's condition — omit it.
  * tests: advised -> scheduled -> sample_collected -> results_received. Planned/"to be completed"/
    "scheduled" is NOT results_received. results_received requires actual results stated.
  * red_flags: suspected_cardiac = chest pain or arm numbness not yet medically cleared (active);
    cleared = evaluated and cleared. severe_bleeding / dvt_suspected / suicidal_ideation likewise.
    Only add a red flag if the profile reports it; "no chest pain" means no flag.
- restrictions: ONLY restrictions a clinician explicitly advised (e.g. "avoid strenuous exercise").
  Do not infer restrictions yourself.
- language: hindi->hi, english->en, hinglish->hinglish, tamil->ta.
- life_stage: pregnant if pregnant; postpartum only if recently delivered / post-delivery; else none.
- diet_type / workout_setting: unknown if not stated."""


def schema() -> dict:
    s = strict_schema(Profile.model_json_schema())
    p = s["properties"]
    p["language"] = {"type": "string", "enum": vocab.LANGUAGES}
    items = lambda k: p[k]["items"]["properties"]
    items("red_flags")["code"] = {"type": "string", "enum": vocab.RED_FLAGS}
    items("issues")["code"] = {"type": "string", "enum": vocab.ISSUES}
    items("tests")["code"] = {"type": "string", "enum": vocab.TESTS}
    items("goals")["code"] = {"type": "string", "enum": vocab.GOALS}
    items("interventions")["code"] = {"type": "string", "enum": vocab.INTERVENTIONS}
    items("restrictions")["code"] = {"type": "string", "enum": vocab.RESTRICTIONS}
    return s


def extract(pep_xml: str, model: str) -> Profile:
    data = chat_json(model, SYSTEM, f"<profile>\n{pep_xml}\n</profile>", schema(), name="profile", max_tokens=4000)
    return Profile(**data)


# ---------- D7: code checks ----------

PLANNED = ["to be ", "scheduled", "pending", "will ", "advised", "next week", "planned"]
NEGATION = re.compile(r"\b(no|not|never|without|ruled out|denies)\b", re.I)
DANGER = {"chest pain": "suspected_cardiac", "numbness": "suspected_cardiac",
          "suicid": "suicidal_ideation", "heavy bleeding": "severe_bleeding"}


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s.lower()).strip()


def code_checks(pep_xml: str, prof: Profile, prev: Profile | None = None) -> list[dict]:
    pep = _norm(pep_xml)
    flags = []

    def flag(kind, fact, why):
        flags.append({"kind": kind, "code": fact.code if hasattr(fact, "code") else str(fact), "why": why})

    facts = prof.red_flags + prof.issues + prof.tests + prof.goals + prof.interventions + prof.restrictions
    for f in facts:
        if _norm(f.quote) not in pep:
            flag("quote_missing", f, "quote not found verbatim in profile")
    for t in prof.tests:
        q = _norm(t.quote)
        if t.status == "results_received":
            if any(w in q for w in PLANNED):
                flag("planned_as_done", t, "quote says planned, status says results received")
            if not re.search(r"\d", q):
                flag("no_proof", t, "results received but no result values in quote")
    for i in prof.issues:
        if i.status == "confirmed" and NEGATION.search(i.quote.split(";")[0][:40]):
            flag("negation", i, "quote is negated, status says confirmed")
    # Safety tripwire: danger words present but the red flag is missing (omission check).
    extracted = {r.code for r in prof.red_flags}
    for word, code in DANGER.items():
        if word in pep and code not in extracted and not re.search(rf"no {word}", pep):
            flag("missed_red_flag", code, f"'{word}' in profile but no {code} extracted")
    # Old-vs-new checks (D7 / D11).
    if prev:
        new_rf = {r.code: r for r in prof.red_flags}
        for r in prev.red_flags:
            if r.status == "active" and r.code not in new_rf:
                flag("flag_vanished", r, "active red flag disappeared without a 'cleared' entry")
        order = {s: n for n, s in enumerate(vocab.TEST_STATUS)}
        new_t = {t.code: t for t in prof.tests}
        for t in prev.tests:
            if t.code in new_t and order[new_t[t.code].status] < order[t.status]:
                flag("status_backwards", t, f"{t.status} -> {new_t[t.code].status}")
        new_i = {i.code for i in prof.issues}
        for i in prev.issues:
            if i.chronic and i.code not in new_i:
                flag("chronic_vanished", i, "chronic issue disappeared")
    return flags


# ---------- D7: LLM verifier on flagged items only, then safer status ----------

VERIFY_SYSTEM = """You check flagged facts extracted from a patient profile. For each flagged fact, read the
profile and decide the correct value. Answer conservatively: if unsure, choose the EARLIER test status
or keep a red flag ACTIVE."""


def verify(pep_xml: str, prof: Profile, flags: list[dict], model: str) -> tuple[Profile, list[dict]]:
    if not flags:
        return prof, []
    sch = {"type": "object", "additionalProperties": False, "required": ["decisions"],
           "properties": {"decisions": {"type": "array", "items": {
               "type": "object", "additionalProperties": False,
               "required": ["code", "kind", "verdict", "corrected_status", "quote"],
               "properties": {
                   "code": {"type": "string"}, "kind": {"type": "string"},
                   "verdict": {"type": "string", "enum": ["extraction_correct", "fix", "unsure"]},
                   "corrected_status": {"type": "string"},
                   "quote": {"type": "string"}}}}}}
    user = f"<profile>\n{pep_xml}\n</profile>\n\nExtracted:\n{prof.model_dump_json()}\n\nFlagged:\n{flags}"
    decisions = chat_json(model, VERIFY_SYSTEM, user, sch, name="verify")["decisions"]
    prof = prof.model_copy(deep=True)
    for d in decisions:
        if d["verdict"] == "extraction_correct":
            continue
        safe = d["verdict"] == "unsure"
        for t in prof.tests:
            if t.code == d["code"]:
                t.status = "scheduled" if safe else (d["corrected_status"] if d["corrected_status"] in vocab.TEST_STATUS else "scheduled")
        for i in prof.issues:
            if i.code == d["code"] and d["kind"] == "negation":
                i.status = "suspected" if safe else (d["corrected_status"] if d["corrected_status"] in ("suspected", "confirmed", "resolved") else "suspected")
        if d["kind"] in ("missed_red_flag", "flag_vanished") and d["code"] in vocab.RED_FLAGS:
            existing = [r for r in prof.red_flags if r.code == d["code"]]
            status = "active" if safe or d["corrected_status"] != "cleared" else "cleared"
            if existing:
                existing[0].status = status
            else:
                from .schemas import RedFlag
                prof.red_flags.append(RedFlag(code=d["code"], status=status, quote=d["quote"]))
    unresolved = [d for d in decisions if d["verdict"] == "unsure"]   # → clinical review queue
    return prof, unresolved
