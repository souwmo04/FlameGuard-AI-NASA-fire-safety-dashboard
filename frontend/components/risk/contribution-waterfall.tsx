"use client";

import { ArrowDown, ArrowUp, Info, Minus } from "lucide-react";
import { motion, useReducedMotion } from "motion/react";

import { cn } from "@/lib/cn";
import { formatRisk } from "@/lib/format";
import type { Contribution, Explanation, ModelInfoResponse } from "@/lib/types";

const TICKS = [0, 25, 50, 75, 100];
const pct = (v: number) => `${Math.min(100, Math.max(0, v))}%`;
const signed = (v: number) => `${v > 0 ? "+" : v < 0 ? "−" : "±"}${Math.abs(v).toFixed(1)}`;

const DIRECTION = {
  raises: { icon: ArrowUp, bar: "bg-risk-high", text: "text-risk-high", word: "raises" },
  lowers: { icon: ArrowDown, bar: "bg-plasma", text: "text-plasma", word: "lowers" },
  neutral: { icon: Minus, bar: "bg-ink-3", text: "text-ink-3", word: "has almost no effect on" },
} as const;

interface Row {
  key: string;
  label: string;
  from: number;
  to: number;
  value: string;
  kind: "base" | "final" | Contribution["direction"];
  sr: string;
}

/** Base bar, one floating bar per contribution (cumulative), then the scenario's total. */
function buildRows(explanation: Explanation, fireRisk: number): Row[] {
  const base = explanation.base_value;
  const rows: Row[] = [
    { key: "base", label: "Average FLEX test", from: 0, to: base, value: formatRisk(base), kind: "base",
      sr: `Average Fire Risk over the FLEX training tests: ${base.toFixed(1)}.` },
  ];
  let running = base;
  for (const c of explanation.contributions) {
    const from = running;
    running += c.impact;
    rows.push({ key: c.key, label: c.label, from, to: running, value: signed(c.impact), kind: c.direction,
      sr: c.direction === "neutral"
        ? `${c.label} has almost no effect (${signed(c.impact)} points), leaving Fire Risk at ${running.toFixed(1)}.`
        : `${c.label} ${DIRECTION[c.direction].word} Fire Risk by ${Math.abs(c.impact).toFixed(1)} points, to ${running.toFixed(1)}.` });
  }
  rows.push({ key: "final", label: "This scenario", from: 0, to: fireRisk, value: formatRisk(fireRisk), kind: "final",
    sr: `Fire Risk for this scenario: ${fireRisk.toFixed(1)}.` });
  return rows;
}

interface WaterfallProps {
  explanation: Explanation;
  fireRisk: number;
  alert: number;
  globalImportance?: ModelInfoResponse["global_importance"];
}

/** Shapley waterfall: from the average FLEX test, each input moves the Fire Risk to this scenario's value. */
export function ContributionWaterfall({ explanation, fireRisk, alert, globalImportance }: WaterfallProps) {
  const reduce = useReducedMotion();
  const rows = buildRows(explanation, fireRisk);

  return (
    <div className="space-y-5">
      <ol className="space-y-2.5">
        {rows.map((r, i) => {
          const lo = Math.min(r.from, r.to);
          const width = Math.abs(r.to - r.from);
          const growsLeft = r.to < r.from;
          const dir = r.kind === "base" || r.kind === "final" ? null : DIRECTION[r.kind];
          const Icon = dir?.icon;
          return (
            <li key={r.key} className="grid grid-cols-[minmax(0,1fr)_auto] items-center gap-x-3 gap-y-1.5 sm:grid-cols-[12.5rem_minmax(0,1fr)_3.5rem]">
              <span className={cn("flex min-w-0 items-center gap-1.5 text-sm", r.kind === "final" ? "font-semibold text-ink" : "text-ink-2")}>
                {Icon && <Icon className={cn("size-3.5 shrink-0", dir.text)} aria-hidden="true" />}
                <span className="min-w-0 truncate" title={r.label}>
                  {r.label.split(" (")[0]}
                  {r.label.includes(" (") && <span className="ml-1 text-xs text-ink-3">{r.label.slice(r.label.indexOf(" (") + 1)}</span>}
                </span>
              </span>
              <span
                className={cn("text-right font-mono text-sm tabular-nums sm:order-last", dir ? dir.text : "text-ink",
                  r.kind === "final" && "font-semibold text-flame")}
                aria-hidden="true"
              >
                {r.value}
              </span>
              <div className="relative col-span-2 h-7 overflow-hidden rounded-md bg-white/[0.025] sm:col-span-1" aria-hidden="true">
                {TICKS.map((t) => (
                  <span key={t} className="absolute inset-y-0 w-px bg-white/[0.05]" style={{ left: pct(t) }} />
                ))}
                <span className="absolute inset-y-0 w-px bg-risk-elevated/40" style={{ left: pct(alert) }} />
                {dir && <span className="absolute inset-y-0 border-l border-dashed border-ink-3/60" style={{ left: pct(r.from) }} />}
                <motion.span
                  className={cn(
                    "absolute inset-y-1.5 rounded-[5px]",
                    r.kind === "base" && "bg-ink-3/45",
                    r.kind === "final" && "bg-gradient-to-r from-flame to-ember shadow-[0_0_18px_-4px_rgb(251_146_60/0.7)]",
                    dir?.bar,
                  )}
                  style={{ left: pct(lo), width: `max(3px, ${pct(width)})`, transformOrigin: growsLeft ? "right" : "left" }}
                  initial={reduce ? false : { scaleX: 0, opacity: 0.4 }}
                  animate={{ scaleX: 1, opacity: 1 }}
                  transition={{ duration: 0.6, delay: 0.1 + i * 0.16, ease: [0.22, 1, 0.36, 1] }}
                />
              </div>
              <span className="sr-only">{r.sr}</span>
            </li>
          );
        })}
      </ol>

      {/* axis */}
      <div className="grid grid-cols-1 gap-x-3 sm:grid-cols-[12.5rem_minmax(0,1fr)_3.5rem]" aria-hidden="true">
        <span className="hidden sm:block" />
        <div className="relative h-4 font-mono text-[0.625rem] text-ink-3">
          {TICKS.map((t) => (
            <span key={t} className="absolute -translate-x-1/2 first:translate-x-0 last:-translate-x-full" style={{ left: pct(t) }}>{t}</span>
          ))}
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-x-4 gap-y-1.5 text-xs text-ink-3">
        <span className="flex items-center gap-1.5"><ArrowUp className="size-3 text-risk-high" aria-hidden="true" />raises Fire Risk</span>
        <span className="flex items-center gap-1.5"><ArrowDown className="size-3 text-plasma" aria-hidden="true" />lowers Fire Risk</span>
        <span className="flex items-center gap-1.5"><span className="h-3 w-px bg-risk-elevated/70" aria-hidden="true" />alert threshold {formatRisk(alert)}</span>
      </div>

      {globalImportance && globalImportance.length > 0 && (
        <p className="text-xs leading-relaxed text-ink-3">
          <span className="text-ink-2">For context, across all FLEX tests</span> the model&apos;s average influence splits{" "}
          {globalImportance
            .slice()
            .sort((a, b) => b.share - a.share)
            .map((g) => `${g.player.split(" (")[0]} ${Math.round(g.share * 100)}%`)
            .join(" · ")}
          .
        </p>
      )}

      <details className="group rounded-xl border border-white/[0.06] bg-white/[0.02] p-3.5 text-sm">
        <summary className="flex cursor-pointer list-none items-center gap-2 text-ink-2">
          <Info className="size-4 text-prov-explanation" aria-hidden="true" /> How is this calculated — and what it does not mean
        </summary>
        <div className="mt-3 space-y-2 text-xs leading-relaxed text-ink-3">
          <p>{explanation.method}</p>
          <p className="text-ink-2">{explanation.note}</p>
        </div>
      </details>
    </div>
  );
}
