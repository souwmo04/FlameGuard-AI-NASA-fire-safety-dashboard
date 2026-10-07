"use client";

import { motion } from "motion/react";

import { OUTCOME_COLORS, OUTCOME_LABEL } from "@/lib/chart-theme";
import type { SimilarResponse } from "@/lib/types";

/** The most similar tested FLEX conditions (observed outcomes) for the analysed scenario. */
export function NearestTests({ similar }: { similar: SimilarResponse }) {
  return (
    <ul className="grid gap-3 md:grid-cols-3">
      {similar.items.map((item, i) => {
        const e = item.experiment;
        const supp = e.suppressant === "none" ? "N₂ only" : e.suppressant === "CO2" ? `CO₂ ${e.co2_percent}%` : `He ${e.he_percent}%`;
        return (
          <motion.li
            key={e.test_id}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 + i * 0.07 }}
            className="space-y-3 rounded-xl border border-white/[0.06] bg-white/[0.02] p-4"
          >
            <div className="flex items-center justify-between">
              <span className="font-mono text-xs text-ink-3">TEST {String(e.test_id).padStart(3, "0")} · {e.flex_identifier}</span>
              <span className="font-mono text-xs font-semibold text-plasma">{Math.round(item.similarity)}%</span>
            </div>
            <div className="h-1 overflow-hidden rounded-full bg-white/[0.06]">
              <motion.div className="h-full rounded-full bg-plasma" initial={{ width: 0 }} animate={{ width: `${item.similarity}%` }}
                transition={{ duration: 0.8, delay: 0.15 + i * 0.07 }} />
            </div>
            <p className="text-xs text-ink-2">
              O₂ {e.oxygen_percent}% · {supp} · {e.droplet_diameter_mm} mm · {e.pressure_level.replace("atm", " atm")}
            </p>
            <p className="flex items-center gap-2 text-sm font-medium" style={{ color: OUTCOME_COLORS[e.outcome] }}>
              <span className="size-2 rounded-full" style={{ background: OUTCOME_COLORS[e.outcome] }} aria-hidden="true" />
              <span className="text-ink">{OUTCOME_LABEL[e.outcome]}</span>
            </p>
          </motion.li>
        );
      })}
    </ul>
  );
}
