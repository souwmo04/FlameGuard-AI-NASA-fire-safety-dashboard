"use client";

import { ArrowRight, CircleCheck, TriangleAlert } from "lucide-react";
import { motion } from "motion/react";

import { AnimatedNumber } from "@/components/ui/animated-number";
import { GlassCard } from "@/components/ui/glass-card";
import { ProvenanceBadge } from "@/components/ui/provenance-badge";
import { RiskBadge } from "@/components/ui/risk-badge";
import { cn } from "@/lib/cn";
import { describeConditions } from "@/lib/conditions";
import { formatPercent, formatRisk } from "@/lib/format";
import type { WhatIfResponse } from "@/lib/types";

import { SCENARIO, type ScenarioKey } from "./scenario-style";
import { ScenarioTag } from "./scenario-tag";

function Side({ which, result }: { which: ScenarioKey; result: WhatIfResponse["a"] }) {
  const s = SCENARIO[which];
  const supported = result.supported_by_data && result.in_tested_range;
  return (
    <div className="flex min-w-0 flex-col items-center gap-2.5 text-center">
      <ScenarioTag which={which} />
      <p className={cn("font-display text-6xl font-bold tabular-nums leading-none tracking-tight sm:text-7xl", s.text)}>
        <AnimatedNumber value={result.fire_risk} format={formatRisk} />
      </p>
      <p className="text-xs text-ink-3">Fire Risk · {formatPercent(result.sustained_probability)} chance it keeps burning</p>
      <RiskBadge level={result.risk_level} />
      <p className={cn("flex items-center gap-1.5 text-xs", supported ? "text-ink-3" : "text-risk-elevated")}>
        {supported ? <CircleCheck className="size-3.5 text-risk-low" aria-hidden="true" /> : <TriangleAlert className="size-3.5" aria-hidden="true" />}
        {supported ? "Close to tested FLEX conditions" : "Extrapolation — far from tested conditions"}
      </p>
      <p className="max-w-xs text-xs text-ink-3">{describeConditions(result.conditions)}</p>
    </div>
  );
}

/** A → B headline: both Fire Risk scores and the change between them. */
export function ComparisonHero({ data, busy }: { data: WhatIfResponse; busy?: boolean }) {
  const d = data.delta;
  const up = d > 0.05;
  const down = d < -0.05;
  const word = up ? "higher" : down ? "lower" : "about the same";
  return (
    <GlassCard glow className={cn("@container h-full p-5 transition-opacity sm:p-7", busy && "opacity-70")}>
      <div className="mb-5 flex flex-wrap items-center justify-between gap-2">
        <h2 className="font-display text-base font-semibold text-ink">Scenario comparison</h2>
        <ProvenanceBadge kind="prediction" compact />
      </div>
      <div className="grid items-center gap-6 @xl:grid-cols-[1fr_auto_1fr]">
        <Side which="a" result={data.a} />
        <div className="flex flex-col items-center gap-2" aria-live="polite">
          <ArrowRight className="hidden size-6 text-ink-3 @xl:block" aria-hidden="true" />
          <motion.span
            key={Math.sign(Math.round(d * 10))}
            initial={{ scale: 0.85, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            className={cn(
              "rounded-full border px-4 py-1.5 font-mono text-lg font-semibold tabular-nums",
              up && "border-risk-high/40 bg-risk-high/10 text-risk-high",
              down && "border-plasma/40 bg-plasma/10 text-plasma",
              !up && !down && "border-white/10 bg-white/[0.04] text-ink-2",
            )}
          >
            <AnimatedNumber value={d} format={(n) => `${n > 0.05 ? "+" : n < -0.05 ? "−" : "±"}${Math.abs(n).toFixed(1)}`} />
          </motion.span>
          <p className="max-w-[11rem] text-center text-xs text-ink-3">
            B is <span className="font-semibold text-ink-2">{word}</span>
            {(up || down) && <> by {Math.abs(d).toFixed(1)} points</>}
          </p>
        </div>
        <Side which="b" result={data.b} />
      </div>
    </GlassCard>
  );
}
