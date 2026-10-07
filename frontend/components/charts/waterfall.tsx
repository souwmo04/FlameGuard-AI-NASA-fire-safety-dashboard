"use client";

import { ArrowDown, ArrowUp, Minus, TriangleAlert } from "lucide-react";
import { motion, useReducedMotion } from "motion/react";

import { cn } from "@/lib/cn";
import { formatRisk } from "@/lib/format";

const TICKS = [0, 25, 50, 75, 100];
const pct = (v: number) => `${Math.min(100, Math.max(0, v))}%`;

export const signed = (v: number) => `${v > 0 ? "+" : v < 0 ? "−" : "±"}${Math.abs(v).toFixed(1)}`;

export type StepDirection = "raises" | "lowers" | "neutral";

export const DIRECTION = {
  raises: { icon: ArrowUp, bar: "bg-risk-high", text: "text-risk-high", word: "raises" },
  lowers: { icon: ArrowDown, bar: "bg-plasma", text: "text-plasma", word: "lowers" },
  neutral: { icon: Minus, bar: "bg-ink-3", text: "text-ink-3", word: "has almost no effect on" },
} as const;

export interface WaterfallRow {
  key: string;
  label: string;
  /** smaller text after the label, e.g. "O₂ 21% → 18%" */
  detail?: string;
  from: number;
  to: number;
  value: string;
  /** "total" rows are drawn from 0; steps float from the previous total */
  kind: "total" | StepDirection;
  /** Tailwind classes for a total bar (defaults to grey) */
  barClass?: string;
  valueClass?: string;
  emphasis?: boolean;
  /** marks a step that leaves the tested FLEX region */
  warning?: string;
  sr: string;
}

/** Horizontal Fire Risk waterfall on a fixed 0–100 axis, bars growing in sequence. */
export function Waterfall({ rows, alert, labelWidth = "12.5rem" }: { rows: WaterfallRow[]; alert: number; labelWidth?: string }) {
  const reduce = useReducedMotion();
  const cols = { gridTemplateColumns: `var(--wf-cols)` } as const;
  const vars = { ["--wf-label" as string]: labelWidth };

  return (
    // Layout follows the panel's width (container query), not the viewport: labels sit beside the bars only when
    // the panel is wide enough, otherwise above them.
    <div className="@container">
      <div className="space-y-3 [--wf-cols:minmax(0,1fr)_auto] @lg:[--wf-cols:var(--wf-label)_minmax(0,1fr)_3.5rem]" style={vars}>
        <ol className="space-y-2.5">
          {rows.map((r, i) => {
            const lo = Math.min(r.from, r.to);
            const width = Math.abs(r.to - r.from);
            const dir = r.kind === "total" ? null : DIRECTION[r.kind];
            const Icon = dir?.icon;
            return (
              <li key={r.key} className="grid items-center gap-x-3 gap-y-1.5" style={cols}>
                <span className={cn("flex min-w-0 items-center gap-1.5 text-sm", r.emphasis ? "font-semibold text-ink" : "text-ink-2")}>
                  {Icon && <Icon className={cn("size-3.5 shrink-0", dir.text)} aria-hidden="true" />}
                  <span className="min-w-0 truncate" title={r.detail ? `${r.label} ${r.detail}` : r.label}>
                    {r.label}
                    {r.detail && <span className="ml-1 text-xs font-normal text-ink-3">{r.detail}</span>}
                  </span>
                  {r.warning && <TriangleAlert className="size-3.5 shrink-0 text-risk-elevated" aria-label={r.warning} />}
                </span>
                <span
                  className={cn("text-right font-mono text-sm tabular-nums @lg:order-last", dir ? dir.text : "text-ink",
                    r.emphasis && "font-semibold", r.valueClass)}
                  aria-hidden="true"
                >
                  {r.value}
                </span>
                <div className="relative col-span-2 h-7 overflow-hidden rounded-md bg-white/[0.025] @lg:col-span-1" aria-hidden="true">
                  {TICKS.map((t) => (
                    <span key={t} className="absolute inset-y-0 w-px bg-white/[0.05]" style={{ left: pct(t) }} />
                  ))}
                  <span className="absolute inset-y-0 w-px bg-risk-elevated/40" style={{ left: pct(alert) }} />
                  {dir && <span className="absolute inset-y-0 border-l border-dashed border-ink-3/60" style={{ left: pct(r.from) }} />}
                  <motion.span
                    className={cn("absolute inset-y-1.5 rounded-[5px]", dir ? dir.bar : (r.barClass ?? "bg-ink-3/45"),
                      r.warning && "opacity-60 [background-image:repeating-linear-gradient(135deg,transparent_0_4px,rgb(0_0_0/0.35)_4px_7px)]")}
                    style={{ left: pct(lo), width: `max(3px, ${pct(width)})`, transformOrigin: r.to < r.from ? "right" : "left" }}
                    initial={reduce ? false : { scaleX: 0 }}
                    animate={{ scaleX: 1 }}
                    transition={{ duration: 0.6, delay: 0.1 + i * 0.16, ease: [0.22, 1, 0.36, 1] }}
                  />
                </div>
                <span className="sr-only">{r.sr}{r.warning ? ` ${r.warning}` : ""}</span>
              </li>
            );
          })}
        </ol>

        <div className="grid gap-x-3" style={cols} aria-hidden="true">
          <span className="hidden @lg:block" />
          <div className="relative col-span-2 h-4 font-mono text-[0.625rem] text-ink-3 @lg:col-span-1">
            {TICKS.map((t) => (
              <span key={t} className="absolute -translate-x-1/2 first:translate-x-0 last:-translate-x-full" style={{ left: pct(t) }}>{t}</span>
            ))}
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-x-4 gap-y-1.5 pt-1 text-xs text-ink-3">
          <span className="flex items-center gap-1.5"><ArrowUp className="size-3 text-risk-high" aria-hidden="true" />raises Fire Risk</span>
          <span className="flex items-center gap-1.5"><ArrowDown className="size-3 text-plasma" aria-hidden="true" />lowers Fire Risk</span>
          <span className="flex items-center gap-1.5"><span className="h-3 w-px bg-risk-elevated/70" aria-hidden="true" />alert threshold {formatRisk(alert)}</span>
        </div>
      </div>
    </div>
  );
}
