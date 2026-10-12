"""Generate the synthetic tip library (prototype step 2).

Generator model is deliberately a different family from the judge (self-preference bias).
Tags written here are the ground truth: the brief says assume the library is tagged as specified.
"""

import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from feed import vocab
from feed.llm import USAGE, chat_json, cost, strict_schema
from feed.schemas import Tip

GENERATOR = "google/gemini-3.1-pro-preview"
OUT = Path(__file__).resolve().parents[1] / "data" / "library.json"

SYSTEM = """You write a care-tip library for Disha, an Indian AI health coach. Each tip is ONE short
vertical video (30-60s) explaining one thing. You output pipeline metadata in English plus
language variants (what the user sees).

Tag rules — follow exactly, these tags are ground truth for a safety-critical system:
- conditions: issues the tip helps with (use codes from the enum only).
- contraindications: flags for which this tip would be UNSAFE or inappropriate. Examples:
  high-exertion exercise -> suspected_cardiac, pregnant, dvt_suspected (and knee_pain if high impact);
  fasting -> type2_diabetes, pregnant; sugary food -> type2_diabetes; salty food -> hypertension;
  deep abdominal work -> pregnant, postpartum_early. Leave empty if safe for everyone it targets.
- exertion: physical effort the tip asks for (none for pure education).
- requires_confirmed_diagnosis: a condition code ONLY if the tip assumes the viewer already HAS that
  diagnosis (e.g. "Living with hypothyroidism"). Otherwise null. Test-preparation tips are null.
- sensitive: true for sexual/intimate health or mental-health crisis topics.
- universally_safe: true ONLY if safe for anyone with zero screening (no exercise, no diet change,
  no supplements) — e.g. how to talk to Disha, drinking water, basic sleep hygiene.
- is_reinforcement_for_flag: a red-flag code ONLY for tips that urge seeking medical care for it.
- general_wellness: true if useful broadly, not tied to a specific condition.
- interventions: prescribed interventions this tip reinforces (codes from the enum).
- tip_type: why (explains cause) / what (explains a thing) / how_to (steps) / myth (myth-busting).
- topic_cluster: short snake_case cluster name.
- review_status: approved unless the batch instructions ask otherwise. evidence_level: A strong .. D weak.
- variants: write each requested language. Hindi in Devanagari, Hinglish in Roman script, Tamil in
  Tamil script, English in English. title <= 8 words, hook 1 sentence, transcript 50-80 words.
- canonical_description: 1-2 English sentences describing exactly what the video says.
- tip_id: short unique snake_case slug.
Never invent codes outside the enums."""

# (count, theme + required traps). Languages default to hi + en unless stated.
BATCHES = [
    (10, "Period pain and cramps. Include TWO near-duplicate tips that both explain why cramps happen "
         "(same message, different wording). Tag two tips with 'dysmenorrhea' instead of 'menstrual_pain'. "
         "Include one tip reinforcing warm_compress and one reinforcing ginger_turmeric_drink."),
    (8, "Irregular cycles, PCOS, bloating around periods. Include one 'Living with PCOS' tip "
        "(requires_confirmed_diagnosis=pcos). Include one tip with review_status=expired."),
    (8, "Sleep for night-shift workers. Tag at least three with 'circadian_rhythm' instead of "
        "'shift_work_sleep'. Include tips reinforcing sleep_block (fixed daytime sleep, blackout curtains)."),
    (6, "General insomnia and sleep hygiene. Two must be universally_safe. One tip only in Tamil (ta)."),
    (10, "Weight loss nutrition, Indian home food. Include: one intermittent-fasting tip "
         "(contraindicated type2_diabetes, pregnant), one sugary festive dessert swap that still contains sugar "
         "(contraindicated type2_diabetes), two non-veg recipes (diet=nonveg), one night_shift_meal_plan tip, "
         "one meal_photo_logging tip."),
    (10, "Exercise. Include: three high-exertion workouts (HIIT, running, jump rope) with proper "
         "contraindications; two gym-only tips (setting=gym); three low-exertion home workouts using a mat/chair/wall "
         "(setting=home); two strength_training_plan tips for men building muscle (sex=male, goal muscle_gain)."),
    (8, "Pain: lower back pain, knee pain, leg swelling. Tag two leg-swelling tips with 'edema'. "
        "Include one leg_elevation tip and one warm_compress tip. One high-impact knee exercise contraindicated knee_pain."),
    (7, "Pelvic floor and sexual wellness after childbirth. Kegel tips (interventions kegel) — tag some "
        "with 'pelvic_floor'. All must be sensitive=true. sex=female."),
    (9, "Blood tests and deficiencies. Include three test-preparation tips (thyroid_panel, iron_panel, vitamin_d prep; "
        "requires_confirmed_diagnosis=null). Include 'Living with hypothyroidism' "
        "(requires_confirmed_diagnosis=hypothyroidism) and 'Diet for iron-deficiency anaemia' "
        "(requires_confirmed_diagnosis=iron_deficiency) and one vitamin D sunlight tip."),
    (7, "Pregnancy: nausea, glucose tolerance test prep, pregnancy-safe walking. life_stage=pregnant. "
        "Include one tip with review_status=pending."),
    (9, "Type 2 diabetes, hypertension, cholesterol. Include 'Managing type 2 diabetes' "
        "(requires_confirmed_diagnosis=type2_diabetes), walk_after_meals, low_gi_diet, salt_reduction. "
        "Tag two with 'blood_sugar'. One tip Hinglish only."),
    (7, "Stress and anxiety: breathing_exercise, short walks, journaling. One sensitive mental-health tip. "
        "Two tips English only (en)."),
    (6, "Safety reinforcement and onboarding. Include: 'Chest pain or arm numbness? Get checked now' "
        "(is_reinforcement_for_flag=suspected_cardiac); 'Sudden leg pain and swelling? Seek care' "
        "(is_reinforcement_for_flag=dvt_suspected); three universally_safe onboarding tips "
        "(how to talk to Disha, drinking water, morning sunlight); one postpartum recovery basics tip."),
    (5, "Long-tail topics outside the usual list: burning feet at night, hair fall, mouth ulcers, dark circles, "
        "dry skin in winter. Leave conditions EMPTY (no matching code exists) and set general_wellness=true; "
        "describe the topic clearly in canonical_description."),
]


def generation_schema() -> dict:
    s = strict_schema(Tip.model_json_schema())
    p = s["properties"]
    p.pop("published")
    p["conditions"]["items"] = {"type": "string", "enum": vocab.ISSUES + vocab.TAG_ONLY_ISSUES}
    p["goals"]["items"] = {"type": "string", "enum": vocab.GOALS}
    p["contraindications"]["items"] = {"type": "string", "enum": vocab.CONTRA_FLAGS}
    p["interventions"]["items"] = {"type": "string", "enum": vocab.INTERVENTIONS}
    p["requires_confirmed_diagnosis"] = {"anyOf": [{"type": "string", "enum": vocab.ISSUES}, {"type": "null"}]}
    p["is_reinforcement_for_flag"] = {"anyOf": [{"type": "string", "enum": vocab.RED_FLAGS}, {"type": "null"}]}
    p["variants"]["items"]["properties"]["language"] = {"type": "string", "enum": vocab.LANGUAGES}
    s["required"] = list(p.keys())
    return {"type": "object", "properties": {"tips": {"type": "array", "items": s}},
            "required": ["tips"], "additionalProperties": False}


def run_batch(spec):
    n, theme = spec
    user = f"Write exactly {n} tips. Theme and required items:\n{theme}\n" \
           "Unless the theme says otherwise, give each tip two variants: hi and en."
    return chat_json(GENERATOR, SYSTEM, user, generation_schema(), name="tips", temperature=0.7,
                     max_tokens=20000)["tips"]


def main():
    with ThreadPoolExecutor(max_workers=7) as pool:
        results = list(pool.map(run_batch, BATCHES))
    OUT.with_suffix(".raw.json").write_text(json.dumps(results, ensure_ascii=False))
    tips, seen = [], set()
    for batch in results:
        for t in batch:
            tid = t["tip_id"]
            while tid in seen:
                tid += "_b"
            seen.add(tid)
            t["tip_id"] = tid
            tips.append(Tip(**t).model_dump(mode="json"))
    OUT.write_text(json.dumps(tips, ensure_ascii=False, indent=1))
    print(f"{len(tips)} tips → {OUT.name}; cost ${cost(GENERATOR):.3f}; usage {USAGE}")


if __name__ == "__main__":
    main()
