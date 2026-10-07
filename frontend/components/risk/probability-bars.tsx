"use client";

import { motion } from "motion/react";

import { formatPercent } from "@/lib/format";

/** Two complementary probabilities as labelled, animated bars. */
export function ProbabilityBars({ sustained, extinction }: { sustained: number; extinction: number }) {
  const rows = [
    { label: "Sustained combustion", value: sustained, color: "from-flame-strong to-ember", text: "text-flame" },
    { label: "Self-extinction", value: extinction, color: "from-plasma-strong to-plasma", text: "text-plasma" },
  ];
  return (
    <div className="grid gap-4 sm:grid-cols-2">
      {rows.map((r, i) => (
        <div key={r.label} className="space-y-2">
          <div className="flex items-baseline justify-between">
            <span className="label-caps">{r.label}</span>
            <span className={`font-display text-2xl font-semibold tabular-nums ${r.text}`}>{formatPercent(r.value)}</span>
          </div>
          <div className="h-2 overflow-hidden rounded-full bg-white/[0.06]" role="presentation">
            <motion.div
              className={`h-full rounded-full bg-gradient-to-r ${r.color}`}
              initial={{ width: 0 }}
              animate={{ width: `${r.value * 100}%` }}
              transition={{ duration: 0.9, delay: 0.1 + i * 0.08, ease: [0.22, 1, 0.36, 1] }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}
