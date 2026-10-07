"""Ask FlameGuard: retrieval, grounding checks, fallbacks, streaming and rate limiting.

The language model is replaced by a fake so tests are offline, free and deterministic.
"""

import dataclasses
import json
import re

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import create_app
from app.services import ask as ask_service
from app.services.llm import LLMError


def make_client(**overrides):
    settings = dataclasses.replace(get_settings(), **{"ask_per_minute": 100, **overrides})
    return TestClient(create_app(settings))


@pytest.fixture(scope="module")
def offline():
    """No API key: retrieval-only mode."""
    with make_client(llm_api_key=None) as c:
        yield c


@pytest.fixture(scope="module")
def online():
    with make_client(llm_api_key="test-key") as c:
        yield c


def fake_llm(text):
    def _stream(settings, messages, **kwargs):
        assert "Answer ONLY from the numbered passages" in messages[0]["content"]
        assert "Passages:" in messages[1]["content"]
        yield from re.findall(r"\S+\s*", text)  # word-sized deltas, spaces kept
    return _stream


def test_status_lists_sources_without_exposing_key(online):
    s = online.get("/api/ask/status").json()
    assert s["llm_configured"] is True and s["model"] and s["chunks"] > 300
    kinds = {src["kind"] for src in s["sources"]}
    assert kinds == {"nasa", "project", "live"}
    assert "test-key" not in json.dumps(s)


def test_retrieval_only_without_key(offline):
    r = offline.post("/api/ask", json={"question": "Why was pressure dropped from the model?"}).json()
    assert r["mode"] == "retrieval_only" and r["answer"] is None
    assert r["passages"] and r["passages"][0]["n"] == 1
    assert any(p["source_id"] == "decisions" for p in r["passages"])
    assert "No language-model API key" in r["warnings"][0]


def test_off_topic_question_finds_nothing(offline):
    r = offline.post("/api/ask", json={"question": "What is the capital of France?"}).json()
    assert r["mode"] == "no_match" and r["passages"] == []


def test_named_test_is_pinned_with_observed_values(offline):
    r = offline.post("/api/ask", json={"question": "What happened in test FLEX-094?"}).json()
    first = r["passages"][0]
    assert first["kind"] == "live" and first["location"] == "Test 94"
    assert "NASA observed data for FLEX test 94" in first["text"]
    assert any(p["section"] == "Appendix A — Test FLEX-094" for p in r["passages"])


def test_live_facts_match_the_dataset(offline):
    r = offline.post("/api/ask", json={"question": "How many FLEX tests are in the dataset and what were the outcomes?"}).json()
    live = [p for p in r["passages"] if p["source_id"] == "flameguard-live"]
    assert live and "274 FLEX droplet tests" in " ".join(p["text"] for p in live)


def test_llm_answer_with_valid_citations(online, monkeypatch):
    monkeypatch.setattr(ask_service, "stream_chat", fake_llm("Pressure was dropped after stress tests [1][2]."))
    r = online.post("/api/ask", json={"question": "Why was pressure dropped from the model?"}).json()
    assert r["mode"] == "llm" and r["answer"].startswith("Pressure was dropped")
    assert r["cited"] == [1, 2] and r["warnings"] == [] and r["provenance"] == "interpretation"


def test_uncited_and_invalid_citations_are_flagged(online, monkeypatch):
    monkeypatch.setattr(ask_service, "stream_chat", fake_llm("Something without a source [42]."))
    r = online.post("/api/ask", json={"question": "Why was pressure dropped from the model?"}).json()
    assert r["cited"] == []
    assert any("do not exist (42)" in w for w in r["warnings"])


def test_llm_failure_degrades_to_passages(online, monkeypatch):
    def broken(*args, **kwargs):
        raise LLMError("The free language-model quota is used up for the moment. Please try again in a minute.")
        yield  # pragma: no cover
    monkeypatch.setattr(ask_service, "stream_chat", broken)
    r = online.post("/api/ask", json={"question": "Why was pressure dropped from the model?"}).json()
    assert r["mode"] == "retrieval_only" and "quota" in r["warnings"][0] and r["passages"]


def test_stream_emits_meta_tokens_done(online, monkeypatch):
    monkeypatch.setattr(ask_service, "stream_chat", fake_llm("Oxygen matters most [1]."))
    with online.stream("POST", "/api/ask/stream", json={"question": "Which input matters most to the model?"}) as r:
        assert r.headers["content-type"].startswith("text/event-stream")
        events = [line.split(": ", 1)[1] for line in r.iter_lines() if line.startswith("event: ")]
    assert events[0] == "meta" and events[-1] == "done" and events.count("token") == 4


def test_question_validation(offline):
    assert offline.post("/api/ask", json={"question": "hi"}).status_code == 422
    assert offline.post("/api/ask", json={"question": "x" * 501}).status_code == 422


def test_rate_limit():
    with make_client(llm_api_key=None, ask_per_minute=2) as c:
        ask_service_api = __import__("app.api.ask", fromlist=["_hits"])
        ask_service_api._hits.clear()
        codes = [c.post("/api/ask", json={"question": "What is FLEX?"}).status_code for _ in range(3)]
        assert codes == [200, 200, 429]
        ask_service_api._hits.clear()


# --- the OpenAI-compatible client itself (no network: httpx.MockTransport) --------------------

def _settings_with_key():
    return dataclasses.replace(get_settings(), llm_api_key="sk-secret", llm_base_url="https://llm.example/v1", llm_model="m")


def test_stream_chat_parses_openai_sse():
    import httpx
    from app.services.llm import stream_chat

    body = ('data: {"choices":[{"delta":{"role":"assistant"}}]}\n\n'
            'data: {"choices":[{"delta":{"content":"Hello "}}]}\n\n'
            ': keep-alive comment\n\n'
            'data: {"choices":[{"delta":{"content":"[1]."}}]}\n\n'
            'data: [DONE]\n\n')
    seen = {}

    def handler(request):
        seen["auth"] = request.headers["authorization"]
        seen["body"] = json.loads(request.content)
        return httpx.Response(200, text=body, headers={"content-type": "text/event-stream"})

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        out = "".join(stream_chat(_settings_with_key(), [{"role": "user", "content": "q"}], client=client))
    assert out == "Hello [1]."
    assert seen["auth"] == "Bearer sk-secret" and seen["body"]["stream"] is True and seen["body"]["model"] == "m"


@pytest.mark.parametrize("status,phrase", [(401, "key was rejected"), (429, "quota"), (503, "temporarily unavailable")])
def test_stream_chat_errors_are_user_safe(status, phrase):
    import httpx
    from app.services.llm import stream_chat

    def handler(request):
        return httpx.Response(status, json={"error": {"message": "secret internal detail sk-secret"}})

    with httpx.Client(transport=httpx.MockTransport(handler)) as client, pytest.raises(LLMError) as err:
        list(stream_chat(_settings_with_key(), [], client=client))
    assert phrase in str(err.value) and "sk-secret" not in str(err.value)
