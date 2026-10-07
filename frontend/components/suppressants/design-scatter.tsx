"use client";

import { useMemo } from "react";
import {
  CartesianGrid,
  ReferenceArea,
  ReferenceLine,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
  ZAxis,
} from "recharts";

import { ChartTooltip } from "@/components/charts/chart-tooltip";
import { OutcomeShape } from "@/components/charts/outcome-shape";
import { AXIS, GRID, OUTCOME_COLORS, OUTCOME_LABEL, OUTCOME_SHAPES, OUTCOME_SHORT, type Outcome } from "@/lib/chart-theme";
import type { SeriesEstimate, SuppressantObservation } from "@/lib/types";

import { SUPPRESSANT_STYLE } from "./suppressant-style";

interface Point {
  x: number;
  y: number;
  id: number;
  outcome: Outcome;
  d0: number | null;
}

const OUTCOMES: Outcome[] = ["Extinction", "Completion", "Disruption"];

interface Props {
  observed: SuppressantObservation[];
  fuel: string;
  pressure: string;
  suppressant: "CO2" | "He";
  estimate?: SeriesEstimate;
}

/**
 * How NASA actually tested a suppressant: O₂ against added CO₂ or He, plus the N₂-only tests at 0%.
 * The downward diagonal is the test design (more suppressant came with less oxygen) — the reason
 * the two effects cannot be separated.
 */
export function DesignScatter({ observed, fuel, pressure, suppressant, estimate }: Props) {
  const series = useMemo(() => {
    const s: Record<Outcome, Point[]> = { Extinction: [], Completion: [], Disruption: [] };
    for (const o of observed) {
      if (o.fuel !== fuel || o.pressure_level !== pressure) continue;
      if (o.suppressant !== suppressant && o.suppressant !== "none") continue;
      const pct = suppressant === "CO2" ? o.co2_percent : o.he_percent;
      // small deterministic spread so repeated conditions stay visible
      s[o.outcome as Outcome].push({ x: pct + ((o.test_id % 5) - 2) * 0.35, y: o.oxygen_percent, id: o.test_id, outcome: o.outcome as Outcome, d0: o.droplet_diameter_mm });
    }
    return s;
  }, [observed, fuel, pressure, suppressant]);
  const total = OUTCOMES.reduce((n, o) => n + series[o].length, 0);
  const est = estimate?.estimable && estimate.o2_50_percent !== null ? estimate : undefined;
  const label = SUPPRESSANT_STYLE[suppressant].label;

  return (
    <figure aria-label={`${total} observed tests: oxygen versus added ${label}, by outcome`} className="space-y-3">
      <div className="h-80 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <ScatterChart margin={{ top: 10, right: 16, bottom: 22, left: -6 }}>
            <CartesianGrid {...GRID} />
            {est && est.ci_low_percent !== null && est.ci_high_percent !== null && (
              <ReferenceArea y1={est.ci_low_percent} y2={est.ci_high_percent} fill={SUPPRESSANT_STYLE[suppressant].color} fillOpacity={0.08} ifOverflow="hidden" />
            )}
            {est && (
              <ReferenceLine y={est.o2_50_percent!} stroke={SUPPRESSANT_STYLE[suppressant].color} strokeDasharray="5 4"
                label={{ value: `O₂₅₀ ${est.o2_50_percent!.toFixed(1)}%`, position: "insideTopRight", fill: SUPPRESSANT_STYLE[suppressant].color, fontSize: 11 }} />
            )}
            <XAxis type="number" dataKey="x" domain={[-2, 52]} ticks={[0, 10, 20, 30, 40, 50]} unit="%" {...AXIS}
              label={{ value: `Added ${label} (% of atmosphere; 0 = N₂ only)`, position: "insideBottom", offset: -12, fill: "#7b8aa3", fontSize: 11 }} />
            <YAxis type="number" dataKey="y" domain={[10, 36]} ticks={[12, 16, 20, 24, 28, 32, 36]} unit="%" {...AXIS} />
            <ZAxis range={[50, 50]} />
            <Tooltip
              cursor={{ stroke: "rgb(255 255 255 / 0.15)" }}
              content={({ active, payload }) => {
                if (!active || !payload?.length) return null;
                const p = payload[0].payload as Point;
                return <ChartTooltip title={`Test ${p.id} · ${OUTCOME_LABEL[p.outcome]}`} rows={[
                  { label: "Oxygen", value: `${p.y}%` },
                  { label: label, value: `${Math.max(0, Math.round(p.x))}%` },
                  { label: "Droplet", value: p.d0 !== null ? `${p.d0} mm` : "—" },
                ]} />;
              }}
            />
            {OUTCOMES.map((o) => (
              <Scatter key={o} name={OUTCOME_LABEL[o]} data={series[o]} fill={OUTCOME_COLORS[o]} shape={OUTCOME_SHAPES[o]}
                fillOpacity={0.9} stroke="#0b1020" strokeWidth={1} isAnimationActive={false} />
            ))}
          </ScatterChart>
        </ResponsiveContainer>
      </div>
      <figcaption className="flex flex-wrap items-center gap-x-4 gap-y-1.5 text-xs text-ink-3">
        {OUTCOMES.map((o) => (
          <span key={o} className="flex items-center gap-1.5"><OutcomeShape outcome={o} />{OUTCOME_SHORT[o]} ({series[o].length})</span>
        ))}
        {est ? (
          <span>Dashed line: O₂₅₀ for this {label} series, band = 95% interval.</span>
        ) : (
          <span>No O₂₅₀ line: this {label} series is not estimable.</span>
        )}
      </figcaption>
    </figure>
  );
}
