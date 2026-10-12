"""Controlled vocabulary shared by tip tags and the structured profile (D3, D12).

Tips and profiles use the same codes, so most matching is exact. A small
synonym/relation map (built offline once, clinician-reviewed) covers codes
that mean the same thing; embeddings handle whatever is still unmatched.
"""

ISSUES = [
    "menstrual_pain", "cycle_irregularity", "pcos", "bloating",
    "shift_work_sleep", "insomnia", "fatigue", "stress", "anxiety",
    "lower_back_pain", "knee_pain", "leg_swelling",
    "vaginal_laxity", "postpartum_recovery",
    "hypothyroidism", "iron_deficiency", "vitamin_d_deficiency",
    "type2_diabetes", "hypertension", "high_cholesterol",
    "pregnancy_nausea", "acid_reflux", "constipation",
    "overweight", "muscle_soreness",
]

# Codes that only appear as tip tags (synonyms of profile codes) — exercised by the synonym map.
TAG_ONLY_ISSUES = ["circadian_rhythm", "dysmenorrhea", "pelvic_floor", "edema", "blood_sugar"]

RED_FLAGS = ["suspected_cardiac", "suicidal_ideation", "severe_bleeding", "dvt_suspected"]

# Context flags that tips can be contraindicated against (red flags + life stages + conditions).
CONTRA_FLAGS = RED_FLAGS + ["pregnant", "postpartum_early", "type2_diabetes", "hypertension", "knee_pain"]

TESTS = ["thyroid_panel", "iron_panel", "vitamin_d", "hba1c", "lipid_panel", "glucose_tolerance"]
TEST_STATUS = ["advised", "scheduled", "sample_collected", "results_received"]  # D7 ladder

GOALS = ["weight_loss", "muscle_gain", "better_sleep", "stress_reduction", "glucose_control",
         "healthy_pregnancy", "pain_relief", "regular_cycles"]

INTERVENTIONS = [
    "kegel", "sleep_block", "ginger_turmeric_drink", "warm_compress", "night_shift_meal_plan",
    "meal_photo_logging", "walk_after_meals", "strength_training_plan", "breathing_exercise",
    "low_gi_diet", "small_frequent_meals", "salt_reduction", "leg_elevation",
]

RESTRICTIONS = ["no_high_exertion", "no_fasting", "low_salt", "low_sugar"]

LANGUAGES = ["hi", "en", "hinglish", "ta"]
CLOSE_LANGUAGES = {"hi": ["hinglish"], "hinglish": ["hi"], "en": [], "ta": []}  # D2 step 2

SYNONYMS = {
    "shift_work_sleep": ["circadian_rhythm"],
    "insomnia": ["circadian_rhythm"],
    "menstrual_pain": ["dysmenorrhea"],
    "vaginal_laxity": ["pelvic_floor"],
    "postpartum_recovery": ["pelvic_floor"],
    "leg_swelling": ["edema"],
    "type2_diabetes": ["blood_sugar"],
}


def expand(code: str) -> list[str]:
    """A profile code plus its synonyms — the free daily lookup from D12."""
    return [code] + SYNONYMS.get(code, [])
