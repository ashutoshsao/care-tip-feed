"""Data shapes: tip library (D1, D3) and structured profile (D7, D10)."""

from datetime import date
from typing import Literal, Optional

from pydantic import BaseModel

Sex = Literal["any", "female", "male"]
LifeStage = Literal["any", "pregnant", "postpartum"]
Exertion = Literal["none", "low", "moderate", "high"]
TipType = Literal["why", "what", "how_to", "myth"]


# ---------- Tip library (D1, D3) ----------

class Variant(BaseModel):
    """One language version: everything the user sees lives here (D1)."""
    language: str
    title: str
    hook: str
    description: str
    transcript: str
    duration_s: int


class Tip(BaseModel):
    """Language-neutral concept: pipeline metadata in English (D1, D3)."""
    tip_id: str
    canonical_description: str
    # relevance
    conditions: list[str] = []
    goals: list[str] = []
    sex: Sex = "any"
    min_age: int = 0
    max_age: int = 120
    life_stage: LifeStage = "any"
    general_wellness: bool = False
    universally_safe: bool = False          # D18 cold-start set
    diet: Literal["any", "veg", "nonveg"] = "any"
    setting: Literal["any", "home", "gym"] = "any"
    # safety
    contraindications: list[str] = []        # CONTRA_FLAGS codes
    exertion: Exertion = "none"
    requires_confirmed_diagnosis: Optional[str] = None   # D5
    sensitive: bool = False                  # D6
    is_reinforcement_for_flag: Optional[str] = None      # D4 pinned tip
    prep_for_test: Optional[str] = None                  # shown only while that test is pending
    # clinical governance
    review_status: Literal["approved", "pending", "expired"] = "approved"
    evidence_level: Literal["A", "B", "C", "D"] = "B"
    # intervention link
    interventions: list[str] = []
    # variety
    tip_type: TipType = "what"
    topic_cluster: str = ""
    # ops
    published: date = date(2026, 1, 1)
    variants: list[Variant] = []


# ---------- Structured profile (D7, D10) ----------

class RedFlag(BaseModel):
    code: str
    status: Literal["active", "cleared"]
    quote: str


class Issue(BaseModel):
    code: str
    status: Literal["suspected", "confirmed", "resolved"]
    severity: Literal["mild", "moderate", "severe"]
    chronic: bool
    quote: str


class Test(BaseModel):
    code: str
    status: Literal["advised", "scheduled", "sample_collected", "results_received"]
    result_summary: Optional[str]
    quote: str


class Coded(BaseModel):
    code: str
    quote: str


class Other(BaseModel):
    """Out-of-vocabulary fact: matched by embeddings, logged to grow the vocabulary (D12)."""
    text: str
    quote: str


class Profile(BaseModel):
    language: str
    sex: Literal["female", "male"]
    age: int
    life_stage: Literal["none", "pregnant", "postpartum"]
    diet_type: Literal["veg", "nonveg", "unknown"]
    workout_setting: Literal["home", "gym", "unknown"]
    red_flags: list[RedFlag]
    issues: list[Issue]
    tests: list[Test]
    goals: list[Coded]
    interventions: list[Coded]
    restrictions: list[Coded]
    other: list[Other]

    def flags(self) -> set[str]:
        """Active context flags that tips can be contraindicated against."""
        f = {r.code for r in self.red_flags if r.status == "active"}
        if self.life_stage == "pregnant":
            f.add("pregnant")
        for i in self.issues:
            if i.status == "confirmed" and i.code in ("type2_diabetes", "hypertension", "knee_pain"):
                f.add(i.code)
        return f

    def restriction_codes(self) -> set[str]:
        return {r.code for r in self.restrictions}
