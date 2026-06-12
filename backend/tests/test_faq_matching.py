"""FAQ matching accuracy + language detection, using the offline backend."""
import os

os.environ["EMBEDDING_BACKEND"] = "local"

from app.core.faq_index import detect_language, get_index, reset_index


def setup_function():
    reset_index()


def test_language_detection():
    assert detect_language("टमाटर के पत्ते पीले") == "hi"   # devanagari
    assert detect_language("tamatar ke patte peele") == "hi"  # romanized hindi
    assert detect_language("which fertilizer for tomato") == "en"


def test_known_queries_match_expected_faq():
    index = get_index()
    cases = [
        ("tamatar ke liye kaunsa khaad", "faq_tomato_fertilizer"),
        ("how much urea per acre for wheat", "faq_urea_dose_wheat"),
        ("mere tamatar ke patte peele ho rahe hain", "faq_tomato_yellow_leaves"),
        ("15 litre pump mein kitni dawai", "faq_spray_per_pump"),
        ("mirch me keede lag gaye", "faq_chilli_pest"),
        ("dukaan kitne baje khulti hai", "faq_shop_timing"),
    ]
    correct = 0
    for query, expected_id in cases:
        result = index.best_match(query)
        if result.matched and result.faq.id == expected_id:
            correct += 1
    # Allow one miss; expect strong majority correct.
    assert correct >= len(cases) - 1, f"only {correct}/{len(cases)} matched"


def test_irrelevant_query_is_escalated():
    index = get_index()
    # Nothing in the FAQ set about cricket scores -> should not auto-resolve.
    result = index.best_match("what is the ipl cricket score today")
    assert result.matched is False


def test_scores_are_bounded():
    index = get_index()
    r = index.best_match("tomato fertilizer")
    assert 0.0 <= r.score <= 1.0001
