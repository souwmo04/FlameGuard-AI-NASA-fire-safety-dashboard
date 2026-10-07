"use client";

import { motion } from "motion/react";

import { cn } from "@/lib/cn";
import type { SeriesEstimate } from "@/lib/types";

import { SUPPRESSANT_STYLE, suppKey } from "./suppressant-style";

const LO = 10;
const HI = 36;
const TICKS = [12, 16, 20, 24, 28, 32, 36];
const x = (v: number) => `${((Math.min(HI, Math.max(LO, v)) - LO) / (HI - LO)) * 100}%`;
const w = (a: number, b: number) => `${((Math.min(HI, b) - Math.max(LO, a)) / (HI - LO)) * 100}%`;
const ORDER = { none: 0, CO2: 1, He: 2 } as const;

function Row({ s, i }: { s: SeriesEstimate; i: number }) {
  const st = SUPPRESSANT_STYLE[suppKey(s.suppressant)];
  const est = s.estimable && s.o2_50_percent !== null && s.ci_low_percent !== null && s.ci_high_percent !== null;
  return (
    <li className="grid grid-cols-[minmax(0,1fr)_auto] items-center gap-x-4 gap-y-1.5 py-1.5 @2xl:grid-cols-[8rem_minmax(0,1fr)_11rem]">
      <span className="flex items-center gap-2 text-sm text-ink">
        <span className="size-2.5 shrink-0 rounded-full" style={{ background: st.color }} aria-hidden="true" />
        {st.label}
        <span className="text-xs text-ink-3">n={s.tests}</span>
      </span>
      <span className={cn("text-right font-mono text-xs tabular-nums @2xl:order-last", est ? "text-ink" : "text-ink-3")}>
        {est ? (
          <>{s.o2_50_percent!.toFixed(1)}% <span className="text-ink-3">({s.ci_low_percent!.toFixed(1)}–{s.ci_high_percent!.toFixed(1)})</span></>
        ) : "not estimable"}
      </span>
      <span className="relative col-span-2 h-7 @2xl:col-span-1" aria-hidden="true">
        {TICKS.map((t) => <span key={t} className="absolute inset-y-0 w-px bg-white/[0.05]" style={{ left: x(t) }} />)}
        {/* tested oxygen range */}
        <span className="absolute top-1/2 h-3 -translate-y-1/2 rounded-sm bg-white/[0.06]" style={{ left: x(s.oxygen_tested_min), width: w(s.oxygen_tested_min, s.oxygen_tested_max) }} />
        {est && (
          <>
            <motion.span className="absolute top-1/2 h-1 -translate-y-1/2 rounded-full" style={{ left: x(s.ci_low_percent!), width: w(s.ci_low_percent!, s.ci_high_percent!), background: st.color, opacity: 0.45, transformOrigin: "center" }}
              initial={{ scaleX: 0 }} animate={{ scaleX: 1 }} transition={{ duration: 0.6, delay: 0.1 + i * 0.05 }} />
            <motion.span className="absolute top-1/2 size-3.5 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-space-950"
              style={{ left: x(s.o2_50_percent!), background: st.color, boxShadow: `0 0 12px ${st.color}99` }}
              initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ type: "spring", delay: 0.25 + i * 0.05 }} />
          </>
        )}
        {!est && (
          <span className="absolute inset-0 flex items-center justify-center text-[0.6875rem] text-ink-3">
            {s.sustained} kept burning · {s.extinguished} went out — needs ≥ 3 of each
          </span>
        )}
      </span>
      <span className="sr-only">
        {est
          ? `${st.long}: O₂₅₀ ${s.o2_50_percent!.toFixed(1)}%, 95% interval ${s.ci_low_percent!.toFixed(1)} to ${s.ci_high_percent!.toFixed(1)}%${s.ci_beyond_tested ? ", extending beyond the tested oxygen range" : ""}; tested from ${s.oxygen_tested_min} to ${s.oxygen_tested_max}% O₂.`
          : `${st.long}: not estimable (${s.sustained} kept burning, ${s.extinguished} went out; needs at least 3 of each).`}
      </span>
      {est && s.ci_beyond_tested && (
        <span className="col-span-2 -mt-1 text-[0.6875rem] text-risk-elevated @2xl:col-span-1 @2xl:col-start-2">
          Interval extends beyond the tested O₂ range ({s.oxygen_tested_min}–{s.oxygen_tested_max}%), so its upper end is extrapolated.
        </span>
      )}
    </li>
  );
}

/** O₂₅₀ estimate per fuel × pressure × suppressant series, on one oxygen axis, grouped so like is compared with like. */
export function O2Forest({ estimates }: { estimates: SeriesEstimate[] }) {
  const groups = new Map<string, SeriesEstimate[]>();
  for (const s of estimates) {
    const k = `${s.fuel}|${s.pressure_level}`;
    groups.set(k, [...(groups.get(k) ?? []), s]);
  }
  const keys = [...groups.keys()].sort((a, b) => b.split("|")[1].localeCompare(a.split("|")[1]) || b.localeCompare(a));
  let n = 0;
  return (
    <div className="@container space-y-5">
      <div className="hidden grid-cols-[8rem_minmax(0,1fr)_11rem] gap-x-4 @2xl:grid" aria-hidden="true">
        <span />
        <span className="relative h-4 font-mono text-[0.625rem] text-ink-3">
          {TICKS.map((t) => <span key={t} className="absolute -translate-x-1/2 last:-translate-x-full" style={{ left: x(t) }}>{t}%</span>)}
        </span>
        <span className="text-right label-caps text-[0.625rem]">O₂₅₀ (95% CI)</span>
      </div>
      {keys.map((k) => {
        const [fuel, p] = k.split("|");
        const rows = groups.get(k)!.sort((a, b) => ORDER[suppKey(a.suppressant)] - ORDER[suppKey(b.suppressant)]);
        return (
          <section key={k} aria-label={`${fuel} at ${p}`} className="rounded-xl border border-white/[0.06] bg-white/[0.015] px-3 py-2.5">
            <h3 className="label-caps mb-1 text-[0.625rem] text-ink-2">{fuel === "Heptane" ? "n-Heptane" : "Methanol"} · {p.replace("atm", " atm")}</h3>
            <ul>{rows.map((s) => <Row key={s.suppressant} s={s} i={n++} />)}</ul>
          </section>
        );
      })}
      <p className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-ink-3">
        <span className="flex items-center gap-1.5"><span className="h-3 w-5 rounded-sm bg-white/[0.08]" aria-hidden="true" />O₂ range tested</span>
        <span className="flex items-center gap-1.5"><span className="size-2.5 rounded-full bg-ink-2" aria-hidden="true" />O₂₅₀ estimate</span>
        <span className="flex items-center gap-1.5"><span className="h-1 w-5 rounded-full bg-ink-3" aria-hidden="true" />95% interval</span>
      </p>
    </div>
  );
}
