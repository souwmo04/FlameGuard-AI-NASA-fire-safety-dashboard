"use client";

import { useMemo } from "react";
import {
  CartesianGrid,
  ComposedChart,
  Line,
  ReferenceArea,
  ReferenceDot,
  ReferenceLine,
  ResponsiveContainer,
  Scatter,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { ChartTooltip } from "@/components/charts/chart-tooltip";
import { AXIS, GRID, OUTCOME_LABEL, OUTCOME_SHAPES, RISK_COLORS, type Outcome } from "@/lib/chart-theme";
import { formatRisk } from "@/lib/format";
import type { Conditions, ExperimentSummary, WhatIfResponse } from "@/lib/types";

import { SCENARIO, type ScenarioKey } from "./scenario-style";

type Sweep = NonNullable<WhatIfResponse["sweep"]>;

interface ObservedPoint {
  x: number;
  y: number;
  id: number;
  outcome: Outcome;
  detail: string;
}

const MARKER = "#e2e8f0";

const suppPercent = (c: Conditions) => c.suppressant_percent ?? 0;
const expSuppPercent = (e: ExperimentSummary) => (e.suppressant === "CO2" ? e.co2_percent : e.suppressant === "He" ? e.he_percent : 0);

/**
 * FLEX tests comparable to a scenario along the swept input: same fuel and suppressant (within 5 points),
 * and the other numeric input close (droplet within 0.75 mm for an oxygen sweep, O₂ within 1.5 points for a
 * droplet sweep). Plotted at the top (kept burning) or bottom (went out) — observed outcomes, not risk scores.
 */
export function comparableTests(experiments: ExperimentSummary[], c: Conditions, feature: Sweep["feature"]): ObservedPoint[] {
  return experiments
    .filter((e) => e.fuel === c.fuel && e.suppressant === c.suppressant && Math.abs(expSuppPercent(e) - suppPercent(c)) <= 5)
    .filter((e) =>
      feature === "oxygen"
        ? e.droplet_diameter_mm !== null && Math.abs(e.droplet_diameter_mm - c.droplet_diameter_mm) <= 0.75
        : e.droplet_diameter_mm !== null && Math.abs(e.oxygen_percent - c.oxygen_percent) <= 1.5,
    )
    .map((e) => ({
      x: feature === "oxygen" ? e.oxygen_percent : (e.droplet_diameter_mm as number),
      // stagger overlapping markers slightly so repeated conditions stay visible
      y: e.sustained ? 97 - (e.test_id % 4) * 2 : 3 + (e.test_id % 4) * 2,
      id: e.test_id,
      outcome: e.outcome,
      detail: `O₂ ${e.oxygen_percent}% · ${e.suppressant === "none" ? "no suppressant" : `${e.suppressant === "CO2" ? "CO₂" : "He"} ${expSuppPercent(e)}%`} · ${e.droplet_diameter_mm} mm`,
    }));
}

function Marker({ cx, cy, payload }: { cx?: number; cy?: number; payload?: ObservedPoint }) {
  if (cx === undefined || cy === undefined || !payload) return null;
  const shape = OUTCOME_SHAPES[payload.outcome];
  const r = 4.5;
  return (
    <g>
      <title>{`NASA test ${payload.id}: ${OUTCOME_LABEL[payload.outcome]} (${payload.detail})`}</title>
      {shape === "circle" && <circle cx={cx} cy={cy} r={r} fill="none" stroke={MARKER} strokeWidth={1.5} />}
      {shape === "triangle" && <path d={`M${cx} ${cy - r} L${cx + r} ${cy + r * 0.8} L${cx - r} ${cy + r * 0.8} Z`} fill={MARKER} />}
      {shape === "diamond" && <path d={`M${cx} ${cy - r} L${cx + r} ${cy} L${cx} ${cy + r} L${cx - r} ${cy} Z`} fill={MARKER} />}
    </g>
  );
}

interface SweepChartProps {
  sweep: Sweep;
  a: Conditions;
  b: Conditions;
  /** current Fire Risk of each scenario, marked on its curve */
  aRisk: number;
  bRisk: number;
  alert: number;
  observed: ObservedPoint[];
  observedFor: ScenarioKey | null;
}

/** Fire Risk as one input varies with everything else held at A or B; dashed where the model extrapolates. */
export function SweepChart({ sweep, a, b, aRisk, bRisk, alert, observed, observedFor }: SweepChartProps) {
  const data = useMemo(
    () =>
      sweep.points.map((p) => ({
        x: p.x,
        aAll: p.a,
        bAll: p.b,
        aIn: p.a_supported ? p.a : null,
        bIn: p.b_supported ? p.b : null,
        aSup: p.a_supported,
        bSup: p.b_supported,
      })),
    [sweep],
  );
  const xs = sweep.points.map((p) => p.x);
  const domain: [number, number] = [Math.min(...xs), Math.max(...xs)];
  // round tick values (every 4% O₂ or 0.5 mm) inside the swept range
  const stepSize = sweep.feature === "oxygen" ? 4 : 0.5;
  const ticks: number[] = [];
  for (let t = Math.ceil(domain[0] / stepSize) * stepSize; t <= domain[1] + 1e-9; t += stepSize) ticks.push(Number(t.toFixed(2)));
  const at = (c: Conditions) => (sweep.feature === "oxygen" ? c.oxygen_percent : c.droplet_diameter_mm);
  const unit = sweep.feature === "oxygen" ? "%" : " mm";

  return (
    <figure aria-label={`Fire Risk as ${sweep.label.toLowerCase()} varies, for scenarios A and B`} className="space-y-3">
      <div className="h-80 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={data} margin={{ top: 10, right: 14, bottom: 22, left: -10 }}>
            <ReferenceArea y1={0} y2={alert} fill={RISK_COLORS.LOW} fillOpacity={0.045} ifOverflow="hidden" />
            <ReferenceArea y1={alert} y2={50} fill={RISK_COLORS.ELEVATED} fillOpacity={0.045} ifOverflow="hidden" />
            <ReferenceArea y1={50} y2={100} fill={RISK_COLORS.HIGH} fillOpacity={0.045} ifOverflow="hidden" />
            <CartesianGrid {...GRID} />
            <XAxis type="number" dataKey="x" domain={domain} unit={unit} {...AXIS} ticks={ticks}
              label={{ value: `${sweep.label} (${sweep.unit})`, position: "insideBottom", offset: -12, fill: "#7b8aa3", fontSize: 11 }} />
            <YAxis type="number" domain={[0, 100]} ticks={[0, 25, 50, 75, 100]} {...AXIS} />
            <ReferenceLine y={alert} stroke={RISK_COLORS.ELEVATED} strokeOpacity={0.55} strokeDasharray="4 4" />

            <Line dataKey="aAll" stroke={SCENARIO.a.color} strokeOpacity={0.45} strokeDasharray="5 5" strokeWidth={1.5} dot={false} activeDot={false} isAnimationActive={false} />
            <Line dataKey="bAll" stroke={SCENARIO.b.color} strokeOpacity={0.45} strokeDasharray="5 5" strokeWidth={1.5} dot={false} activeDot={false} isAnimationActive={false} />
            <Line dataKey="aIn" stroke={SCENARIO.a.color} strokeWidth={2.5} dot={false} activeDot={{ r: 4 }} connectNulls={false} animationDuration={700} />
            <Line dataKey="bIn" stroke={SCENARIO.b.color} strokeWidth={2.5} dot={false} activeDot={{ r: 4 }} connectNulls={false} animationDuration={700} />

            <ReferenceLine x={at(a)} stroke={SCENARIO.a.color} strokeOpacity={0.35} />
            <ReferenceLine x={at(b)} stroke={SCENARIO.b.color} strokeOpacity={0.35} />
            <ReferenceDot x={at(a)} y={aRisk} r={6} fill={SCENARIO.a.color} stroke="#05070d" strokeWidth={2} />
            <ReferenceDot x={at(b)} y={bRisk} r={6} fill={SCENARIO.b.color} stroke="#05070d" strokeWidth={2} />

            {observedFor && <Scatter data={observed} dataKey="y" shape={<Marker />} isAnimationActive={false} />}

            <Tooltip
              cursor={{ stroke: "rgb(255 255 255 / 0.18)" }}
              content={({ active, payload }) => {
                const row = payload?.find((p) => p.payload && "aAll" in p.payload)?.payload as (typeof data)[number] | undefined;
                if (!active || !row) return null;
                const fmt = (v: number | null, ok: boolean) => (v === null ? "—" : `${formatRisk(v)}${ok ? "" : " (extrap.)"}`);
                return (
                  <ChartTooltip
                    title={`${sweep.label} ${row.x.toFixed(sweep.feature === "oxygen" ? 1 : 2)}${unit}`}
                    rows={[
                      { label: "Scenario A", value: fmt(row.aAll, row.aSup), color: SCENARIO.a.color },
                      { label: "Scenario B", value: fmt(row.bAll, row.bSup), color: SCENARIO.b.color },
                    ]}
                  />
                );
              }}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
      <figcaption className="flex flex-wrap items-center gap-x-4 gap-y-1.5 text-xs text-ink-3">
        <span className="flex items-center gap-1.5"><span className="h-0.5 w-4 rounded-full" style={{ background: SCENARIO.a.color }} aria-hidden="true" />Scenario A</span>
        <span className="flex items-center gap-1.5"><span className="h-0.5 w-4 rounded-full" style={{ background: SCENARIO.b.color }} aria-hidden="true" />Scenario B</span>
        <span className="flex items-center gap-1.5"><span className="w-4 border-t border-dashed border-ink-3" aria-hidden="true" />dashed = extrapolation</span>
        <span className="flex items-center gap-1.5"><span className="size-2 rounded-full" style={{ background: SCENARIO.b.color }} aria-hidden="true" />dot = current setting</span>
        {observedFor && (
          <span className="flex items-center gap-1.5">
            <svg viewBox="0 0 10 10" className="size-2.5" aria-hidden="true"><path d="M5 0.5 L9.5 9.5 L0.5 9.5 Z" fill={MARKER} /></svg>
            <svg viewBox="0 0 10 10" className="size-2.5" aria-hidden="true"><circle cx="5" cy="5" r="4" fill="none" stroke={MARKER} strokeWidth="1.5" /></svg>
            NASA tests like {SCENARIO[observedFor].letter}: top = kept burning, bottom = went out ({observed.length})
          </span>
        )}
      </figcaption>
    </figure>
  );
}
