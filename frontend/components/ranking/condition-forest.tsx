"use client";

import { ChevronDown } from "lucide-react";
import { AnimatePresence, motion } from "motion/react";
import Link from "next/link";
import { useMemo, useState } from "react";

import { cn } from "@/lib/cn";
import { formatPercent } from "@/lib/format";
import type { ConditionRank } from "@/lib/types";

const TICKS = [0, 25, 50, 75, 100];
const SHOWN = 12;

export const atmosphereLabel = (c: Pick<ConditionRank, "oxygen_percent" | "suppressant" | "co2_percent" | "he_percent">) =>
  `${c.oxygen_percent}% O₂${c.suppressant === "CO2" ? ` + ${c.co2_percent}% CO₂` : c.suppressant === "He" ? ` + ${c.he_percent}% He` : ""}`;

/**
 * Observed share of tests that kept burning, per tested atmosphere, with 95% Wilson intervals.
 * Each row expands to the individual tests so the claim can be checked.
 */
export function ConditionForest({ items, order }: { items: ConditionRank[]; order: "desc" | "asc" }) {
  const [expanded, setExpanded] = useState<string | null>(null);
  const [showAll, setShowAll] = useState(false);
  const sorted = useMemo(
    () => [...items].sort((a, b) => (order === "desc" ? b.observed_rate - a.observed_rate || b.ci_low - a.ci_low : a.observed_rate - b.observed_rate || a.ci_high - b.ci_high)),
    [items, order],
  );
  const rows = showAll ? sorted : sorted.slice(0, SHOWN);

  return (
    <div className="@container space-y-3">
      <div className="hidden grid-cols-[minmax(0,15rem)_minmax(0,1fr)_4.5rem] gap-x-4 @2xl:grid" aria-hidden="true">
        <span />
        <div className="relative h-4 font-mono text-[0.625rem] text-ink-3">
          {TICKS.map((t) => (
            <span key={t} className="absolute -translate-x-1/2 first:translate-x-0 last:-translate-x-full" style={{ left: `${t}%` }}>{t}%</span>
          ))}
        </div>
        <span />
      </div>
      <ol className="space-y-1">
        {rows.map((c, i) => {
          const key = `${c.fuel}-${c.pressure_level}-${c.suppressant}-${c.oxygen_percent}-${c.co2_percent}-${c.he_percent}`;
          const open = expanded === key;
          return (
            <motion.li key={key} layout="position" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: Math.min(i, 12) * 0.03 }}>
              <button
                type="button"
                aria-expanded={open}
                onClick={() => setExpanded(open ? null : key)}
                className="grid w-full grid-cols-[minmax(0,1fr)_auto] items-center gap-x-4 gap-y-1.5 rounded-lg px-2 py-2 text-left transition hover:bg-white/[0.03] @2xl:grid-cols-[minmax(0,15rem)_minmax(0,1fr)_4.5rem]"
              >
                <span className="flex min-w-0 items-center gap-2">
                  <span className="w-5 shrink-0 font-mono text-xs text-ink-3">{i + 1}</span>
                  <span className="min-w-0">
                    <span className="block truncate text-sm text-ink">{atmosphereLabel(c)}</span>
                    <span className="block text-xs text-ink-3">{c.fuel === "Heptane" ? "n-heptane" : "methanol"} · {c.pressure_level.replace("atm", " atm")}</span>
                  </span>
                </span>
                <span className="text-right font-mono text-xs tabular-nums text-ink-2 @2xl:order-last">
                  {c.sustained}/{c.tests}
                  <ChevronDown className={cn("ml-1 inline size-3.5 text-ink-3 transition", open && "rotate-180")} aria-hidden="true" />
                </span>
                <span className="relative col-span-2 h-6 @2xl:col-span-1" aria-hidden="true">
                  {TICKS.map((t) => (
                    <span key={t} className="absolute inset-y-0 w-px bg-white/[0.05]" style={{ left: `${t}%` }} />
                  ))}
                  <motion.span className="absolute top-1/2 h-1 -translate-y-1/2 rounded-full bg-prov-observed/35"
                    initial={{ scaleX: 0 }} animate={{ scaleX: 1 }} style={{ left: `${c.ci_low * 100}%`, width: `${(c.ci_high - c.ci_low) * 100}%`, transformOrigin: "left" }}
                    transition={{ duration: 0.5, delay: 0.1 + Math.min(i, 12) * 0.03 }} />
                  <span className="absolute top-1/2 size-3 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-space-950 bg-prov-observed shadow-[0_0_10px_rgb(34_211_238/0.6)]"
                    style={{ left: `${c.observed_rate * 100}%` }} />
                </span>
                <span className="sr-only">
                  {c.sustained} of {c.tests} tests kept burning ({formatPercent(c.observed_rate)}; 95% interval {formatPercent(c.ci_low)} to {formatPercent(c.ci_high)}).
                </span>
              </button>
              <AnimatePresence initial={false}>
                {open && (
                  <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }} exit={{ height: 0, opacity: 0 }} className="overflow-hidden">
                    <div className="flex flex-wrap items-center gap-1.5 px-2 pb-3 pl-9 text-xs text-ink-3">
                      <span>{formatPercent(c.observed_rate)} kept burning (95% CI {formatPercent(c.ci_low)}–{formatPercent(c.ci_high)}). Tests:</span>
                      {c.test_ids.map((id) => (
                        <Link key={id} href={`/experiments?test=${id}`}
                          className="rounded-md border border-white/10 px-1.5 py-0.5 font-mono text-ink-2 transition hover:border-prov-observed/40 hover:text-prov-observed">
                          {String(id).padStart(3, "0")}
                        </Link>
                      ))}
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.li>
          );
        })}
      </ol>
      {sorted.length > SHOWN && (
        <button type="button" onClick={() => setShowAll((s) => !s)}
          className="rounded-lg border border-white/10 px-3 py-1.5 text-xs text-ink-2 transition hover:border-white/20 hover:text-ink">
          {showAll ? "Show fewer" : `Show all ${sorted.length} conditions`}
        </button>
      )}
      <p className="flex items-center gap-3 text-xs text-ink-3">
        <span className="flex items-center gap-1.5"><span className="size-2.5 rounded-full bg-prov-observed" aria-hidden="true" />observed share that kept burning</span>
        <span className="flex items-center gap-1.5"><span className="h-1 w-5 rounded-full bg-prov-observed/35" aria-hidden="true" />95% interval</span>
      </p>
    </div>
  );
}
