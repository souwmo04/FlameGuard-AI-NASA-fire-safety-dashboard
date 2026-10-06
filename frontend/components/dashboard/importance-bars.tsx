"use client";

import { motion } from "motion/react";

import { formatPercent } from "@/lib/format";
import type { ModelInfoResponse } from "@/lib/types";

const LABELS: Record<string, string> = {
  "atmosphere (O₂ + CO₂ + He)": "Atmosphere (O₂ + CO₂ + He)",
  "droplet size": "Droplet size",
  fuel: "Fuel",
};

/** Mean |Shapley contribution| per input group across the 252 training tests. */
export function ImportanceBars({ model }: { model: ModelInfoResponse }) {
  const rows = [...model.global_importance].sort((a, b) => b.share - a.share);
  const max = Math.max(...rows.map((r) => r.mean_abs_points));
  return (
    <div className="space-y-4">
      <ul className="space-y-3.5">
        {rows.map((r, i) => (
          <li key={r.player} className="space-y-1.5">
            <div className="flex items-baseline justify-between gap-3 text-sm">
              <span className="text-ink-2">{LABELS[r.player] ?? r.player}</span>
              <span className="font-mono text-xs tabular-nums text-ink">
                {r.mean_abs_points.toFixed(1)} pts <span className="text-ink-3">· {formatPercent(r.share)}</span>
              </span>
            </div>
            <div className="h-2 overflow-hidden rounded-full bg-white/[0.05]">
              <motion.div
                className="h-full rounded-full bg-gradient-to-r from-prov-explanation/70 to-prov-explanation"
                initial={{ width: 0 }}
                animate={{ width: `${(r.mean_abs_points / max) * 100}%` }}
                transition={{ duration: 0.9, delay: 0.15 + i * 0.1, ease: [0.22, 1, 0.36, 1] }}
              />
            </div>
          </li>
        ))}
      </ul>
      <p className="text-xs text-ink-3">
        Average size of each input&apos;s contribution to Fire Risk (points), fuel accounted for first. Associations, not causes.
      </p>
    </div>
  );
}
