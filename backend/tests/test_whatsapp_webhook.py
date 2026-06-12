"""End-to-end webhook test with a mocked Twilio inbound payload."""
import os
import tempfile

os.environ["EMBEDDING_BACKEND"] = "local"
# Isolated throwaway log DB per test run.
os.environ["QUERY_LOG_DB"] = os.path.join(tempfile.mkdtemp(), "test_queries.db")

from fastapi.testclient import TestClient

from app.core.faq_index import reset_index
from app.core.query_log import stats
from app.main import app

client = TestClient(app)


def setup_function():
    reset_index()


def _post(body: str, from_number: str = "whatsapp:+919999000011"):
    # Twilio posts application/x-www-form-urlencoded.
    return client.post(
        "/api/v1/whatsapp/inbound",
        data={"Body": body, "From": from_number},
    )


def test_matched_query_returns_twiml_answer():
    resp = _post("tamatar ke liye kaunsa khaad daalein")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("application/xml")
    assert "<Response><Message>" in resp.text
    # The tomato fertilizer answer mentions NPK 19:19:19.
    assert "19:19:19" in resp.text


def test_unmatched_query_returns_fallback():
    resp = _post("tell me yesterday cricket match result")
    assert resp.status_code == 200
    # English fallback copy.
    assert "shop will get back" in resp.text


def test_query_log_records_resolution():
    _post("how much urea per acre for wheat")   # should resolve
    _post("random unrelated gibberish xyz123")  # should escalate
    s = stats()
    assert s["total_queries"] >= 2
    assert s["auto_resolved"] >= 1
    assert s["escalated"] >= 1


def test_faq_search_endpoint():
    resp = client.get("/api/v1/faqs/search", params={"q": "mirch me keede"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["detected_language"] == "hi"
    assert len(data["results"]) >= 1
    assert "score" in data["results"][0]
