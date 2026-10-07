"""Ask FlameGuard endpoints, rate-limited per client so a free LLM quota is not exhausted by one visitor."""

from __future__ import annotations

import time
from collections import defaultdict, deque
from threading import Lock

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse

from app.schemas.responses import AskRequest, AskResponse, AskStatus
from app.services import ask as service
from app.state import AppState, get_state

router = APIRouter(tags=["ask"])

WINDOW_S = 60.0
_hits: dict[str, deque[float]] = defaultdict(deque)
_lock = Lock()


def rate_limit(request: Request, state: AppState = Depends(get_state)) -> None:
    """At most `ask_per_minute` questions per client IP in any 60-second window (in-memory, per process)."""
    limit = state.settings.ask_per_minute
    client = request.client.host if request.client else "unknown"
    now = time.monotonic()
    with _lock:
        q = _hits[client]
        while q and now - q[0] > WINDOW_S:
            q.popleft()
        if len(q) >= limit:
            wait = int(WINDOW_S - (now - q[0])) + 1
            raise HTTPException(status_code=429, detail=f"Too many questions — please wait {wait} s and try again.",
                                headers={"Retry-After": str(wait)})
        q.append(now)


@router.get("/ask/status", response_model=AskStatus, summary="Is the assistant configured, and what does it search?")
def ask_status(state: AppState = Depends(get_state)) -> AskStatus:
    return service.status(state)


@router.post("/ask", response_model=AskResponse, summary="Answer a question from the FLEX report and project docs",
             dependencies=[Depends(rate_limit)])
def ask(body: AskRequest, state: AppState = Depends(get_state)) -> AskResponse:
    return service.ask(state, body.question.strip())


@router.post("/ask/stream", summary="Same as /ask, streamed as server-sent events (meta, token*, done)",
             dependencies=[Depends(rate_limit)], response_class=StreamingResponse)
def ask_stream(body: AskRequest, state: AppState = Depends(get_state)) -> StreamingResponse:
    return StreamingResponse(service.ask_stream(state, body.question.strip()), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})
