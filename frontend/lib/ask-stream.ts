/**
 * Client for POST /api/ask/stream (server-sent events over a fetch body, so a POST body can be sent).
 * Events: `meta` (mode + numbered passages) -> `token`* (answer text deltas) -> `done` (final AskResponse).
 */
import { API_URL, ApiError } from "./api";
import type { AskResponse, Passage } from "./types";

export interface AskMeta {
  mode: AskResponse["mode"];
  model: string | null;
  passages: Passage[];
}

interface Handlers {
  onMeta: (meta: AskMeta) => void;
  onToken: (text: string) => void;
  onDone: (result: AskResponse) => void;
}

export async function askStream(question: string, handlers: Handlers, signal?: AbortSignal): Promise<void> {
  let response: Response;
  try {
    response = await fetch(`${API_URL}/api/ask/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "text/event-stream" },
      body: JSON.stringify({ question }),
      signal,
    });
  } catch (err) {
    if ((err as Error).name === "AbortError") throw err;
    throw new ApiError(`Cannot reach the FlameGuard API at ${API_URL}. Is the backend running?`, null);
  }
  if (!response.ok || !response.body) {
    let message = `The question could not be answered (HTTP ${response.status}).`;
    try {
      const body = await response.json();
      if (typeof body?.detail === "string") message = body.detail;
      else if (Array.isArray(body?.detail)) message = "Please ask a question between 3 and 500 characters.";
    } catch {
      /* keep the generic message */
    }
    throw new ApiError(message, response.status);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  for (;;) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    let cut: number;
    while ((cut = buffer.indexOf("\n\n")) >= 0) {
      const block = buffer.slice(0, cut);
      buffer = buffer.slice(cut + 2);
      const event = /^event: (.*)$/m.exec(block)?.[1];
      const data = /^data: (.*)$/m.exec(block)?.[1];
      if (!event || data === undefined) continue;
      const payload = JSON.parse(data);
      if (event === "meta") handlers.onMeta(payload as AskMeta);
      else if (event === "token") handlers.onToken((payload as { t: string }).t);
      else if (event === "done") handlers.onDone(payload as AskResponse);
    }
  }
}
