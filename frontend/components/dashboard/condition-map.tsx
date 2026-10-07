"use client";

import { useMemo, useState } from "react";
import { CartesianGrid, ResponsiveContainer, Scatter, ScatterChart, Tooltip, XAxis, YAxis, ZAxis } from "recharts";

import { ChartTooltip } from "@/components/charts/chart-tooltip";
import { OutcomeShape } from "@/components/charts/outcome-shape";
import { AXIS, GRID, OUTCOME_COLORS, OUTCOME_LABEL, OUTCOME_SHAPES, type Outcome } from "@/lib/chart-theme";
import { cn } from "@/lib/cn";
import type { ExperimentSummary } from "@/lib/types";

const FUEL_FILTERS = ["All", "Methanol", "Heptane"] as const;
type FuelFilter = (typeof FUEL_FILTERS)[number];

interface Point {
  x: number;
  y: number;
  id: number;
  fuel: string;
  supp: string;
  outcome: Outcome;
}

/** Observed FLEX tests: oxygen vs droplet size, shape and colour = outcome. */
export function ConditionMap({ experiments }: { experiments: ExperimentSummary[] }) {
  const [fuel, setFuel] = useState<FuelFilter>("All");

  const { series, plotted, missing } = useMemo(() => {
    const rows = experiments.filter((e) => fuel === "All" || e.fuel === fuel);
    const withSize = rows.filter((e) => e.droplet_diameter_mm !== null);
    const s: Record<Outcome, Point[]> = { Extinction: [], Completion: [], Disruption: [] };
    for (const e of withSize) {
      s[e.outcome].push({
        x: e.droplet_diameter_mm as number,
        y: e.oxygen_percent,
        id: e.test_id,
        fuel: e.fuel,
        supp: e.suppressant === "none" ? "none" : `${e.suppressant} ${e.suppressant === "CO2" ? e.co2_percent : e.he_percent}%`,
        outcome: e.outcome,
      });
    }
    return { series: s, plotted: withSize.length, missing: rows.length - withSize.length };
  }, [experiments, fuel]);

  return (
    <div className="space-y-3">
      <div role="radiogroup" aria-label="Fuel" className="inline-flex rounded-xl border border-white/[0.08] bg-white/[0.02] p-1">
        {FUEL_FILTERS.map((f) => (
          <button
            key={f}
            type="button"
            role="radio"
            aria-checked={fuel === f}
            onClick={() => setFuel(f)}
            className={cn("rounded-lg px-3 py-1 text-xs font-medium transition", fuel === f ? "bg-flame/15 text-flame" : "text-ink-3 hover:text-ink-2")}
          >
            {f === "Heptane" ? "n-Heptane" : f}
          </button>
        ))}
      </div>
      <figure aria-label={`Scatter of ${plotted} observed tests: oxygen versus droplet diameter by outcome`}>
        <div className="h-72 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <ScatterChart margin={{ top: 8, right: 12, bottom: 18, left: -8 }}>
              <CartesianGrid {...GRID} />
              <XAxis type="number" dataKey="x" name="Droplet diameter" unit=" mm" domain={[1, 5]} {...AXIS}
                label={{ value: "Initial droplet diameter (mm)", position: "insideBottom", offset: -10, fill: "#7b8aa3", fontSize: 11 }} />
              <YAxis type="number" dataKey="y" name="Oxygen" unit="%" domain={[10, 36]} {...AXIS} />
              <ZAxis range={[46, 46]} />
              <Tooltip
                cursor={{ stroke: "rgb(255 255 255 / 0.15)" }}
                content={({ active, payload }) => {
                  if (!active || !payload?.length) return null;
                  const p = payload[0].payload as Point;
                  return <ChartTooltip title={`Test ${p.id} · ${OUTCOME_LABEL[p.outcome]}`} rows={[
                    { label: "Fuel", value: p.fuel === "Heptane" ? "n-heptane" : "methanol" },
                    { label: "Oxygen", value: `${p.y}%`, color: OUTCOME_COLORS[p.outcome] },
                    { label: "Suppressant", value: p.supp },
                    { label: "Droplet", value: `${p.x} mm` },
                  ]} />;
                }}
              />
              {(Object.keys(series) as Outcome[]).map((o) => (
                <Scatter key={o} name={OUTCOME_LABEL[o]} data={series[o]} fill={OUTCOME_COLORS[o]} shape={OUTCOME_SHAPES[o]}
                  fillOpacity={0.85} stroke="#0b1020" strokeWidth={1} isAnimationActive={false} />
              ))}
            </ScatterChart>
          </ResponsiveContainer>
        </div>
        <figcaption className="flex flex-wrap items-center gap-x-4 gap-y-1.5 text-xs text-ink-3">
          {(Object.keys(OUTCOME_COLORS) as Outcome[]).map((o) => (
            <span key={o} className="flex items-center gap-1.5">
              <OutcomeShape outcome={o} /> {OUTCOME_LABEL[o]} ({series[o].length})
            </span>
          ))}
          {missing > 0 && <span>{missing} test{missing > 1 ? "s" : ""} without a reported droplet diameter not shown.</span>}
        </figcaption>
      </figure>
    </div>
  );
}
