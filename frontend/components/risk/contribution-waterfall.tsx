"use client";

import { Info } from "lucide-react";

import { DIRECTION, signed, Waterfall, type WaterfallRow } from "@/components/charts/waterfall";
import { formatRisk } from "@/lib/format";
import type { Explanation, ModelInfoResponse } from "@/lib/types";

/** Base bar, one floating bar per contribution (cumulative), then the scenario's total. */
function buildRows(explanation: Explanation, fireRisk: number): WaterfallRow[] {
  const base = explanation.base_value;
  const rows: WaterfallRow[] = [
    { key: "base", label: "Average FLEX test", from: 0, to: base, value: formatRisk(base), kind: "total",
      sr: `Average Fire Risk over the FLEX training tests: ${base.toFixed(1)}.` },
  ];
  let running = base;
  for (const c of explanation.contributions) {
    const from = running;
    running += c.impact;
    const [label, detail] = c.label.split(" (");
    rows.push({ key: c.key, label, detail: detail ? `(${detail}` : undefined, from, to: running, value: signed(c.impact),
      kind: c.direction,
      sr: c.direction === "neutral"
        ? `${c.label} has almost no effect (${signed(c.impact)} points), leaving Fire Risk at ${running.toFixed(1)}.`
        : `${c.label} ${DIRECTION[c.direction].word} Fire Risk by ${Math.abs(c.impact).toFixed(1)} points, to ${running.toFixed(1)}.` });
  }
  rows.push({ key: "final", label: "This scenario", from: 0, to: fireRisk, value: formatRisk(fireRisk), kind: "total",
    emphasis: true, valueClass: "text-flame",
    barClass: "bg-gradient-to-r from-flame to-ember shadow-[0_0_18px_-4px_rgb(251_146_60/0.7)]",
    sr: `Fire Risk for this scenario: ${fireRisk.toFixed(1)}.` });
  return rows;
}

interface ContributionWaterfallProps {
  explanation: Explanation;
  fireRisk: number;
  alert: number;
  globalImportance?: ModelInfoResponse["global_importance"];
}

/** Shapley waterfall: from the average FLEX test, each input moves the Fire Risk to this scenario's value. */
export function ContributionWaterfall({ explanation, fireRisk, alert, globalImportance }: ContributionWaterfallProps) {
  return (
    <div className="space-y-5">
      <Waterfall rows={buildRows(explanation, fireRisk)} alert={alert} />

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
