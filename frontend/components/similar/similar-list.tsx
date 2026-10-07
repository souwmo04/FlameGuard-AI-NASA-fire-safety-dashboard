"use client";

import { ArrowUpRight } from "lucide-react";
import { motion } from "motion/react";
import Link from "next/link";

import { OutcomeShape } from "@/components/charts/outcome-shape";
import { atmosphereText } from "@/components/experiments/experiment-table";
import { OUTCOME_SHORT } from "@/lib/chart-theme";
import { cn } from "@/lib/cn";
import type { Conditions, SimilarItem } from "@/lib/types";

const fmtSigned = (v: number, digits: number, unit: string) =>
  `${v > 0 ? "+" : "−"}${Math.abs(v).toFixed(digits)}${unit}`;

/** How a tested condition differs from the query, as short chips ("O₂ −1.0", "CO₂ +5%", "d₀ +0.22 mm"). */
function differences(q: Conditions, item: SimilarItem): string[] {
  const e = item.experiment;
  const out: string[] = [];
  const dO2 = e.oxygen_percent - q.oxygen_percent;
  if (Math.abs(dO2) >= 0.05) out.push(`O₂ ${fmtSigned(dO2, 1, " pts")}`);
  const qSupp = q.suppressant ?? "none";
  const ePct = e.suppressant === "CO2" ? e.co2_percent : e.suppressant === "He" ? e.he_percent : 0;
  const qPct = q.suppressant_percent ?? 0;
  const name = (x: string) => (x === "CO2" ? "CO₂" : "He");
  if (e.suppressant !== qSupp) {
    if (e.suppressant === "none") out.push("no suppressant");
    else if (qSupp === "none") out.push(`+${ePct}% ${name(e.suppressant)}`);
    else out.push(`${ePct}% ${name(e.suppressant)} instead`);
  }
  else if (qSupp !== "none" && Math.abs(ePct - qPct) >= 0.5) out.push(`${qSupp === "CO2" ? "CO₂" : "He"} ${fmtSigned(ePct - qPct, 0, " pts")}`);
  if (e.droplet_diameter_mm !== null) {
    const dd = e.droplet_diameter_mm - q.droplet_diameter_mm;
    if (Math.abs(dd) >= 0.01) out.push(`d₀ ${fmtSigned(dd, 2, " mm")}`);
  }
  return out;
}

export function SimilarList({ items, query, hovered, onHover }: {
  items: SimilarItem[];
  query: Conditions;
  hovered: number | null;
  onHover: (id: number | null) => void;
}) {
  return (
    <ol className="space-y-2">
      {items.map((item, i) => {
        const e = item.experiment;
        const diffs = differences(query, item);
        return (
          <motion.li key={e.test_id} initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.05 + i * 0.04 }}>
            <Link
              href={`/experiments?test=${e.test_id}`}
              onMouseEnter={() => onHover(e.test_id)}
              onMouseLeave={() => onHover(null)}
              onFocus={() => onHover(e.test_id)}
              onBlur={() => onHover(null)}
              className={cn("group block rounded-xl border p-3.5 transition",
                hovered === e.test_id ? "border-flame/35 bg-flame/[0.05]" : "border-white/[0.06] bg-white/[0.02] hover:bg-white/[0.04]")}
            >
              <div className="flex items-center justify-between gap-3">
                <span className="min-w-0 truncate font-mono text-xs text-ink-3">
                  <span className="font-semibold text-ink">#{i + 1}</span> · Test {String(e.test_id).padStart(3, "0")}
                </span>
                <span className="flex shrink-0 items-center gap-1.5 whitespace-nowrap text-xs text-ink-2">
                  <OutcomeShape outcome={e.outcome} />{OUTCOME_SHORT[e.outcome]}
                </span>
              </div>
              <div className="mt-2.5 flex items-center gap-3">
                <span className="h-1.5 flex-1 overflow-hidden rounded-full bg-white/[0.06]" aria-hidden="true">
                  <motion.span className="block h-full rounded-full bg-gradient-to-r from-plasma/60 to-plasma"
                    initial={{ width: 0 }} animate={{ width: `${item.similarity}%` }} transition={{ duration: 0.7, delay: 0.1 + i * 0.04 }} />
                </span>
                <span className="w-24 text-right font-mono text-xs tabular-nums text-plasma">{Math.round(item.similarity)}% similar</span>
              </div>
              <p className="mt-2 text-xs text-ink-2">
                <span className="font-mono text-ink-3">{e.flex_identifier}</span> · {e.fuel === "Heptane" ? "n-heptane" : "methanol"} · {atmosphereText(e)} · {e.droplet_diameter_mm} mm · {e.pressure_level.replace("atm", " atm")}
                {e.burn_time_s !== null && <> · burned {e.burn_time_s.toFixed(1)} s</>}
              </p>
              <div className="mt-2 flex flex-wrap items-center gap-1.5">
                {diffs.length === 0 ? (
                  <span className="rounded-md bg-risk-low/10 px-1.5 py-0.5 text-[0.6875rem] text-risk-low">same conditions</span>
                ) : (
                  diffs.map((d) => <span key={d} className="rounded-md bg-white/[0.05] px-1.5 py-0.5 font-mono text-[0.6875rem] text-ink-3">{d}</span>)
                )}
                <ArrowUpRight className="ml-auto size-3.5 text-ink-3 transition group-hover:text-ink" aria-hidden="true" />
              </div>
            </Link>
          </motion.li>
        );
      })}
    </ol>
  );
}
