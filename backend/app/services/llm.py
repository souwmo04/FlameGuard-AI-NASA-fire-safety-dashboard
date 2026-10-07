"""Minimal client for OpenAI-compatible chat APIs (Groq, Gemini's compatibility endpoint, OpenRouter, ...).

Only httpx is needed. Errors are turned into short, user-safe messages: the API key and raw provider
responses are never echoed back to the browser.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from urllib.parse import urlparse

import httpx

from app.config import Settings

TIMEOUT = httpx.Timeout(45.0, connect=10.0)


class LLMError(RuntimeError):
    """A failure the user can be told about in plain words."""


def provider_host(settings: Settings) -> str:
    return urlparse(settings.llm_base_url).hostname or "unknown"


def _error_for(status: int) -> LLMError:
    if status in (401, 403):
        return LLMError("The language-model API key was rejected. Check FLAMEGUARD_LLM_API_KEY.")
    if status == 404:
        return LLMError("The configured language model was not found. Check FLAMEGUARD_LLM_MODEL.")
    if status == 429:
        return LLMError("The free language-model quota is used up for the moment. Please try again in a minute.")
    if status >= 500:
        return LLMError("The language-model service is temporarily unavailable.")
    return LLMError(f"The language-model service returned an error (HTTP {status}).")


def stream_chat(settings: Settings, messages: list[dict], *, max_tokens: int = 700,
                temperature: float = 0.2, client: httpx.Client | None = None) -> Iterator[str]:
    """Yield text deltas from a streamed chat completion."""
    if not settings.llm_api_key:
        raise LLMError("No language-model API key is configured.")
    body = {"model": settings.llm_model, "messages": messages, "max_tokens": max_tokens,
            "temperature": temperature, "stream": True}
    headers = {"Authorization": f"Bearer {settings.llm_api_key}", "Content-Type": "application/json"}
    own = client is None
    client = client or httpx.Client(timeout=TIMEOUT)
    try:
        with client.stream("POST", f"{settings.llm_base_url}/chat/completions", headers=headers, json=body) as r:
            if r.status_code != 200:
                raise _error_for(r.status_code)
            for line in r.iter_lines():
                if not line.startswith("data:"):
                    continue
                data = line[5:].strip()
                if data == "[DONE]":
                    break
                try:
                    choice = json.loads(data)["choices"][0]
                except (ValueError, KeyError, IndexError):
                    continue
                delta = (choice.get("delta") or {}).get("content")
                if delta:
                    yield delta
    except httpx.TimeoutException as exc:
        raise LLMError("The language-model service did not respond in time.") from exc
    except httpx.HTTPError as exc:
        raise LLMError("Could not reach the language-model service.") from exc
    finally:
        if own:
            client.close()
