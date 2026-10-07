"use client";

import { motion } from "motion/react";
import Link from "next/link";

import { OutcomeShape } from "@/components/charts/outcome-shape";
import { atmosphereText } from "@/components/experiments/experiment-table";
import { OUTCOME_SHORT, RISK_COLORS } from "@/lib/chart-theme";
import { formatRisk } from "@/lib/format";
import type { RankingResponse } from "@/lib/types";

/**
 * Ranked FLEX tests. For model rankings each row shows the observed outcome next to the score, so
 * the list doubles as a check of the model; burn-time rankings are purely observed.
 */
export function TestRankingList({ data }: { data: RankingResponse }) {
  const observed = data.by === "burn_time";
  const max = Math.max(...data.items.map((i) => i.value), 1);
  return (
    <ol className="space-y-1.5">
      {data.items.map((item, i) => {
        const e = item.experiment;
        const width = observed ? (item.value / max) * 100 : item.value;
        const color = observed ? "#22d3ee" : e.prediction ? RISK_COLORS[e.prediction.risk_level] : "#7b8aa3";
        return (
          <motion.li key={e.test_id} initial={{ opacity: 0, x: -6 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: Math.min(i, 15) * 0.025 }}>
            <Link href={`/experiments?test=${e.test_id}`}
              className="grid grid-cols-[1.75rem_minmax(0,1fr)_auto] items-center gap-x-3 gap-y-1.5 rounded-lg px-2 py-2 transition hover:bg-white/[0.03] sm:grid-cols-[1.75rem_minmax(0,16rem)_minmax(0,1fr)_auto]">
              <span className="font-mono text-xs text-ink-3">{item.rank}</span>
              <span className="min-w-0">
                <span className="block truncate text-sm text-ink">
                  <span className="font-mono text-xs text-ink-3">{String(e.test_id).padStart(3, "0")}</span> {atmosphereText(e)}
                </span>
                <span className="block text-xs text-ink-3">
                  {e.fuel === "Heptane" ? "n-heptane" : "methanol"} · {e.droplet_diameter_mm !== null ? `${e.droplet_diameter_mm} mm` : "d₀ —"} · {e.pressure_level.replace("atm", " atm")}
                </span>
              </span>
              <span className="col-span-3 flex items-center gap-3 sm:col-span-1 sm:order-none order-last">
                <span className="h-1.5 flex-1 overflow-hidden rounded-full bg-white/[0.06]" aria-hidden="true">
                  <motion.span className="block h-full rounded-full" style={{ background: color }}
                    initial={{ width: 0 }} animate={{ width: `${width}%` }} transition={{ duration: 0.6, delay: 0.05 + Math.min(i, 15) * 0.025 }} />
                </span>
                <span className="flex w-36 shrink-0 items-center gap-1.5 text-xs text-ink-2">
                  <OutcomeShape outcome={e.outcome} />{OUTCOME_SHORT[e.outcome]}
                </span>
              </span>
              <span className="text-right font-mono text-sm font-semibold tabular-nums text-ink">
                {observed ? `${item.value.toFixed(1)} s` : formatRisk(item.value)}
              </span>
            </Link>
          </motion.li>
        );
      })}
    </ol>
  );
}
