import { afterEach, describe, expect, it, vi } from "vitest";

import { askStream } from "./ask-stream";

function sseResponse(chunks: string[]) {
  const encoder = new TextEncoder();
  const body = new ReadableStream({
    start(controller) {
      for (const c of chunks) controller.enqueue(encoder.encode(c));
      controller.close();
    },
  });
  return new Response(body, { status: 200, headers: { "Content-Type": "text/event-stream" } });
}

const noop = { onMeta: () => {}, onToken: () => {}, onDone: () => {} };

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("askStream", () => {
  it("parses meta, tokens and done even when events are split across network chunks", async () => {
    const events = [
      'event: meta\ndata: {"mode":"llm","model":"m","passages":[]}\n\n',
      'event: token\ndata: {"t":"Hello "}\n\n',
      'event: token\ndata: {"t":"[1]."}\n\n',
      'event: done\ndata: {"mode":"llm","answer":"Hello [1].","cited":[1],"warnings":[],"passages":[]}\n\n',
    ].join("");
    // split at awkward places to exercise the buffering
    const chunks = [events.slice(0, 17), events.slice(17, 70), events.slice(70, 71), events.slice(71)];
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(sseResponse(chunks)));

    const tokens: string[] = [];
    let mode = "";
    let answer = "";
    await askStream("Why?", {
      onMeta: (m) => {
        mode = m.mode;
      },
      onToken: (t) => tokens.push(t),
      onDone: (r) => {
        answer = r.answer ?? "";
      },
    });
    expect(mode).toBe("llm");
    expect(tokens.join("")).toBe("Hello [1].");
    expect(answer).toBe("Hello [1].");
  });

  it("surfaces the API's rate-limit message", async () => {
    const body = JSON.stringify({ detail: "Too many questions, please wait 30 s and try again." });
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(body, { status: 429 })));
    await expect(askStream("Why?", noop)).rejects.toThrow("Too many questions");
  });

  it("explains an unreachable backend", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("Failed to fetch")));
    await expect(askStream("Why?", noop)).rejects.toThrow("Is the backend running?");
  });
});
