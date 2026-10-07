"use client";

import { ArrowUp, Bot, CircleAlert, Info, Search, Sparkles, Square, TriangleAlert, User } from "lucide-react";
import { AnimatePresence, motion } from "motion/react";
import { useCallback, useEffect, useRef, useState } from "react";

import { Panel } from "@/components/dashboard/panel";
import { GlassCard } from "@/components/ui/glass-card";
import { PageHeader } from "@/components/ui/page-header";
import { ProvenanceBadge } from "@/components/ui/provenance-badge";
import { useApi } from "@/hooks/use-api";
import { endpoints } from "@/lib/api";
import { askStream, type AskMeta } from "@/lib/ask-stream";
import { cn } from "@/lib/cn";
import type { AskResponse, AskStatus } from "@/lib/types";

import { AnswerText } from "./answer-text";
import { PASSAGE_KIND, PassageCard } from "./passage-card";

const MAX = 500;
const SUGGESTIONS = [
  "Why was pressure removed from the model?",
  "What happened in test FLEX-094?",
  "Can the data rank CO₂ against helium as a suppressant?",
  "How was the model validated, and how accurate is it?",
  "What hardware did FLEX use on the ISS?",
  "What do the LOW, ELEVATED and HIGH risk bands mean?",
];

interface Turn {
  id: number;
  question: string;
  status: "searching" | "writing" | "done" | "error";
  meta?: AskMeta;
  text: string;
  result?: AskResponse;
  error?: string;
}

function StatusPill({ status }: { status?: AskStatus }) {
  if (!status) return null;
  return status.llm_configured ? (
    <span className="inline-flex items-center gap-2 rounded-full border border-prov-interpretation/30 bg-prov-interpretation/10 px-3 py-1 text-xs text-prov-interpretation">
      <Sparkles className="size-3.5" aria-hidden="true" />{status.model} · {status.provider}
    </span>
  ) : (
    <span className="inline-flex items-center gap-2 rounded-full border border-risk-elevated/30 bg-risk-elevated/10 px-3 py-1 text-xs text-risk-elevated">
      <Search className="size-3.5" aria-hidden="true" />Retrieval only — no language-model key configured
    </span>
  );
}

function TurnView({ turn, active, onCite }: { turn: Turn; active: number | null; onCite: (turn: number, n: number) => void }) {
  const passages = turn.result?.passages ?? turn.meta?.passages ?? [];
  const mode = turn.result?.mode ?? turn.meta?.mode;
  const cited = new Set(turn.result?.cited ?? []);
  const valid = new Set(passages.map((p) => p.n));
  const answer = turn.result?.answer ?? turn.text;
  const sid = (n: number) => `turn-${turn.id}-src-${n}`;

  return (
    <motion.article initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="space-y-3" aria-label={`Question: ${turn.question}`}>
      <div className="flex justify-end">
        <div className="flex max-w-[85%] items-start gap-2.5 rounded-2xl rounded-tr-md border border-flame/20 bg-flame/[0.08] px-4 py-2.5 text-sm text-ink">
          <span>{turn.question}</span>
          <User className="mt-0.5 size-4 shrink-0 text-flame" aria-hidden="true" />
        </div>
      </div>

      <GlassCard className="space-y-4 p-4 sm:p-5">
        <header className="flex flex-wrap items-center gap-2">
          <span className="inline-flex size-7 items-center justify-center rounded-lg bg-gradient-to-br from-flame to-ember text-space-950">
            <Bot className="size-4" aria-hidden="true" />
          </span>
          <span className="font-display text-sm font-semibold text-ink">Ask FlameGuard</span>
          {mode === "llm" && <ProvenanceBadge kind="interpretation" compact />}
          {mode === "retrieval_only" && <ProvenanceBadge kind="observed" compact />}
          {turn.result?.model && <span className="font-mono text-[0.6875rem] text-ink-3">{turn.result.model}</span>}
        </header>

        <div aria-live="polite" aria-busy={turn.status === "searching" || turn.status === "writing"}>
          {turn.status === "searching" && (
            <p className="flex items-center gap-2 text-sm text-ink-3">
              <Search className="size-4 animate-pulse text-plasma" aria-hidden="true" />Searching the NASA FLEX report and FlameGuard documentation…
            </p>
          )}
          {turn.status === "error" && (
            <p role="alert" className="flex items-start gap-2 text-sm text-risk-high">
              <CircleAlert className="mt-0.5 size-4 shrink-0" aria-hidden="true" />{turn.error}
            </p>
          )}
          {mode === "llm" && answer && (
            <AnswerText text={answer} valid={valid} active={active} streaming={turn.status === "writing"} onCite={(n) => onCite(turn.id, n)} />
          )}
          {mode === "retrieval_only" && turn.status === "done" && (
            <p className="text-sm text-ink-2">These are the passages that best match your question. Read them directly — no text was generated.</p>
          )}
          {mode === "no_match" && (
            <p className="text-sm text-ink-2">I couldn&apos;t find anything about this in the NASA FLEX report or the FlameGuard documentation, so I won&apos;t guess. Try asking about FLEX, the dataset, the model or the suppressant analysis.</p>
          )}
        </div>

        {turn.result && turn.result.warnings.length > 0 && (
          <ul className="space-y-1.5">
            {turn.result.warnings.map((w) => (
              <li key={w} className="flex items-start gap-2 rounded-lg border border-risk-elevated/25 bg-risk-elevated/[0.06] px-3 py-2 text-xs text-ink-2">
                <TriangleAlert className="mt-0.5 size-3.5 shrink-0 text-risk-elevated" aria-hidden="true" />{w}
              </li>
            ))}
          </ul>
        )}

        {passages.length > 0 && (
          <section aria-label="Sources" className="space-y-2.5">
            <h3 className="label-caps text-[0.625rem]">
              Sources ({passages.length}){turn.result && mode === "llm" ? ` · ${cited.size} cited` : ""}
            </h3>
            <ol className="grid gap-2.5 lg:grid-cols-2">
              {passages.map((p) => (
                <PassageCard key={p.n} passage={p} id={sid(p.n)} cited={mode !== "llm" || !turn.result || cited.has(p.n)} active={active === p.n} />
              ))}
            </ol>
          </section>
        )}

        {turn.result && mode === "llm" && <p className="text-[0.6875rem] leading-relaxed text-ink-3">{turn.result.note}</p>}
      </GlassCard>
    </motion.article>
  );
}

export function AskFlameGuard() {
  const status = useApi<AskStatus>(endpoints.askStatus);
  const [turns, setTurns] = useState<Turn[]>([]);
  const [input, setInput] = useState("");
  const [active, setActive] = useState<{ turn: number; n: number } | null>(null);
  const abort = useRef<AbortController | null>(null);
  const nextId = useRef(1);
  const endRef = useRef<HTMLDivElement>(null);
  const busy = turns.some((t) => t.status === "searching" || t.status === "writing");

  const update = (id: number, patch: Partial<Turn> | ((t: Turn) => Partial<Turn>)) =>
    setTurns((ts) => ts.map((t) => (t.id === id ? { ...t, ...(typeof patch === "function" ? patch(t) : patch) } : t)));

  const send = useCallback(async (question: string) => {
    const q = question.trim();
    if (q.length < 3 || busy) return;
    const id = nextId.current++;
    setTurns((ts) => [...ts, { id, question: q, status: "searching", text: "" }]);
    setInput("");
    const controller = new AbortController();
    abort.current = controller;
    try {
      await askStream(q, {
        onMeta: (meta) => update(id, { meta, status: meta.mode === "llm" ? "writing" : "searching" }),
        onToken: (t) => update(id, (turn) => ({ text: turn.text + t })),
        onDone: (result) => update(id, { result, status: "done" }),
      }, controller.signal);
      update(id, (turn) => (turn.status === "done" ? {} : { status: "error", error: "The answer stream ended unexpectedly." }));
    } catch (err) {
      const aborted = (err as Error).name === "AbortError";
      update(id, (turn) => ({ status: aborted && turn.text ? "done" : "error", error: aborted ? "Stopped." : (err as Error).message }));
    } finally {
      abort.current = null;
    }
  }, [busy]);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [turns.length]);

  const cite = (turn: number, n: number) => {
    setActive({ turn, n });
    document.getElementById(`turn-${turn}-src-${n}`)?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  };

  useEffect(() => {
    if (!active) return;
    const t = setTimeout(() => setActive(null), 2400);
    return () => clearTimeout(t);
  }, [active]);

  const sources = status.data?.sources ?? [];

  return (
    <div className="space-y-6 lg:space-y-8">
      <PageHeader
        eyebrow="Ask FlameGuard"
        title="Ask FlameGuard"
        subtitle="Questions answered from NASA's FLEX report and FlameGuard's own documentation — every claim cited, nothing invented."
        actions={<StatusPill status={status.data} />}
      />

      <div className="grid gap-4 xl:grid-cols-[minmax(0,8fr)_minmax(0,4fr)] xl:gap-6">
        <div className="min-w-0 space-y-5">
          {turns.length === 0 && (
            <GlassCard glow className="space-y-4 p-5 sm:p-7">
              <div className="flex items-center gap-3">
                <span className="inline-flex size-10 items-center justify-center rounded-xl bg-gradient-to-br from-flame to-ember text-space-950">
                  <Sparkles className="size-5" aria-hidden="true" />
                </span>
                <div>
                  <h2 className="font-display text-lg font-semibold text-ink">What would you like to know?</h2>
                  <p className="text-sm text-ink-3">Try one of these, or ask your own question.</p>
                </div>
              </div>
              <div className="flex flex-wrap gap-2">
                {SUGGESTIONS.map((s) => (
                  <button key={s} type="button" onClick={() => send(s)}
                    className="rounded-xl border border-white/10 bg-white/[0.03] px-3 py-2 text-left text-sm text-ink-2 transition hover:border-flame/30 hover:bg-flame/[0.06] hover:text-ink">
                    {s}
                  </button>
                ))}
              </div>
            </GlassCard>
          )}

          <AnimatePresence initial={false}>
            {turns.map((t) => <TurnView key={t.id} turn={t} active={active?.turn === t.id ? active.n : null} onCite={cite} />)}
          </AnimatePresence>
          <div ref={endRef} />

          <form
            onSubmit={(e) => { e.preventDefault(); send(input); }}
            className="sticky bottom-20 z-10 md:bottom-4"
          >
            <GlassCard className="flex items-end gap-2 bg-space-900/90 p-2.5 shadow-2xl backdrop-blur-xl">
              <label htmlFor="ask-input" className="sr-only">Your question</label>
              <textarea
                id="ask-input"
                value={input}
                maxLength={MAX}
                rows={1}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    send(input);
                  }
                }}
                placeholder="Ask about FLEX, the data, the model or suppressants…"
                className="max-h-40 min-h-11 flex-1 resize-none bg-transparent px-2.5 py-2.5 text-sm text-ink placeholder:text-ink-3 focus:outline-none [field-sizing:content]"
              />
              <span className={cn("hidden pb-3 font-mono text-[0.6875rem] sm:block", input.length > MAX - 50 ? "text-risk-elevated" : "text-ink-3")}>
                {input.length}/{MAX}
              </span>
              {busy ? (
                <button type="button" onClick={() => abort.current?.abort()} aria-label="Stop generating"
                  className="inline-flex size-11 shrink-0 items-center justify-center rounded-xl border border-white/15 text-ink transition hover:bg-white/[0.06]">
                  <Square className="size-4 fill-current" aria-hidden="true" />
                </button>
              ) : (
                <button type="submit" disabled={input.trim().length < 3} aria-label="Ask"
                  className="inline-flex size-11 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-flame to-ember text-space-950 shadow-[0_0_24px_-6px_rgb(251_146_60/0.7)] transition disabled:opacity-40">
                  <ArrowUp className="size-5" aria-hidden="true" />
                </button>
              )}
            </GlassCard>
          </form>
        </div>

        <div className="space-y-4 xl:sticky xl:top-20 xl:self-start xl:space-y-6">
          <Panel title="Knowledge base" description={status.data ? `${status.data.chunks} passages · ${status.data.retrieval} search` : "Loading…"} delay={0.05}>
            <ul className="space-y-2.5">
              {sources.map((s) => {
                const kind = PASSAGE_KIND[s.kind];
                const Icon = kind.icon;
                return (
                  <li key={s.source_id} className="flex items-start gap-2.5">
                    <Icon className={cn("mt-0.5 size-4 shrink-0", kind.tone.split(" ")[0])} aria-hidden="true" />
                    <span className="min-w-0 text-xs">
                      <span className="block text-ink-2">{s.title}</span>
                      <span className="font-mono text-ink-3">{s.chunks} passage{s.chunks === 1 ? "" : "s"}</span>
                    </span>
                  </li>
                );
              })}
            </ul>
          </Panel>
          <Panel title="How it works" delay={0.1}>
            <ol className="space-y-2.5 text-xs leading-relaxed text-ink-2">
              <li className="flex gap-2"><span className="font-mono text-flame">1</span>Your question is matched against the report and docs by meaning and by keywords.</li>
              <li className="flex gap-2"><span className="font-mono text-flame">2</span>The best passages are numbered and given to the language model with strict rules: answer only from them and cite every claim.</li>
              <li className="flex gap-2"><span className="font-mono text-flame">3</span>Citations are checked; uncited or invalid ones are flagged. Without a model key you get the passages themselves.</li>
            </ol>
            <p className="mt-3 flex gap-2 text-[0.6875rem] text-ink-3">
              <Info className="mt-0.5 size-3.5 shrink-0" aria-hidden="true" />
              Generated text can still be wrong — check the cited passages. Not a certified fire-safety system.
              {status.data && ` Limit: ${status.data.per_minute_limit} questions per minute.`}
            </p>
          </Panel>
        </div>
      </div>
    </div>
  );
}
