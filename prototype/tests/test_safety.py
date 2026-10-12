"""Safety filter is plain code (D4/D5), so it gets plain tests."""

from feed.pipeline import safety_reason
from feed.schemas import Issue, Profile, RedFlag, Test, Variant

V = [Variant(language="hi", title="t", hook="h", description="d", transcript="x", duration_s=30)]


def profile(**kw):
    base = dict(language="hi", sex="female", age=27, life_stage="none", diet_type="nonveg", workout_setting="home",
                red_flags=[], issues=[], tests=[], goals=[], interventions=[], restrictions=[], other=[])
    return Profile(**{**base, **kw})


def tip(**kw):
    from feed.schemas import Tip
    return Tip(**{"tip_id": "x", "canonical_description": "d", "variants": V, **kw})


CARDIAC = [RedFlag(code="suspected_cardiac", status="active", quote="chest pain")]


def test_red_flag_blocks_contraindicated_tip():
    assert "contraindicated" in safety_reason(tip(contraindications=["suspected_cardiac"], exertion="high"),
                                              profile(red_flags=CARDIAC))


def test_cleared_flag_unblocks():
    cleared = [RedFlag(code="suspected_cardiac", status="cleared", quote="cleared")]
    assert safety_reason(tip(contraindications=["suspected_cardiac"]), profile(red_flags=cleared)) is None


def test_diagnosis_lock_while_test_pending():
    p = profile(tests=[Test(code="thyroid_panel", status="scheduled", result_summary=None, quote="to be done")])
    assert "diagnosis lock" in safety_reason(tip(requires_confirmed_diagnosis="hypothyroidism"), p)


def test_diagnosis_unlocks_when_confirmed():
    p = profile(issues=[Issue(code="iron_deficiency", status="confirmed", severity="moderate", chronic=False, quote="q")])
    assert safety_reason(tip(requires_confirmed_diagnosis="iron_deficiency"), p) is None


def test_language_without_variant_is_skipped():
    assert "no ta variant" in safety_reason(tip(), profile(language="ta"))


def test_hinglish_falls_back_to_hindi():
    assert safety_reason(tip(), profile(language="hinglish")) is None


def test_expired_review_blocked():
    assert "review expired" in safety_reason(tip(review_status="expired"), profile())
