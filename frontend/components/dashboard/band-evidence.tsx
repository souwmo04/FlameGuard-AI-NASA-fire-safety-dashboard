"use client";

import { Bar, BarChart, CartesianGrid, Cell, ErrorBar, LabelList, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { ChartTooltip } from "@/components/charts/chart-tooltip";
import { AXIS, GRID, RISK_COLORS } from "@/lib/chart-theme";
import { formatPercent } from "@/lib/format";
import type { ModelInfoResponse } from "@/lib/types";

/** For each risk band: how often FLEX tests the model placed there (out-of-fold) actually kept burning. */
export function BandEvidence({ model }: { model: ModelInfoResponse }) {
  const data = model.bands.map((b) => ({
    band: b.level,
    range: `${b.score_from.toFixed(0)}–${b.score_to.toFixed(0)}`,
    rate: b.observed_sustained_rate,
    err: [b.observed_sustained_rate - b.ci_low, b.ci_high - b.observed_sustained_rate] as [number, number],
    tests: b.tests,
    sustained: b.sustained,
    ci: `${formatPercent(b.ci_low)}–${formatPercent(b.ci_high)}`,
  }));
  return (
    <figure aria-label="Observed share of tests that kept burning in each risk band">
      <div className="h-56 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 22, right: 8, bottom: 0, left: -18 }}>
            <CartesianGrid {...GRID} vertical={false} />
            <XAxis dataKey="band" {...AXIS} />
            <YAxis domain={[0, 1]} tickFormatter={(v: number) => formatPercent(v)} {...AXIS} />
            <Tooltip
              cursor={{ fill: "rgb(255 255 255 / 0.04)" }}
              content={({ active, payload }) => {
                if (!active || !payload?.length) return null;
                const d = payload[0].payload as (typeof data)[number];
                return <ChartTooltip title={`${d.band} band · Fire Risk ${d.range}`} rows={[
                  { label: "Kept burning", value: formatPercent(d.rate), color: RISK_COLORS[d.band] },
                  { label: "95% interval", value: d.ci },
                  { label: "Tests", value: `${d.sustained} of ${d.tests}` },
                ]} />;
              }}
            />
            <Bar dataKey="rate" radius={[6, 6, 0, 0]} maxBarSize={64}>
              {data.map((d) => <Cell key={d.band} fill={RISK_COLORS[d.band]} fillOpacity={0.85} />)}
              <ErrorBar dataKey="err" width={8} stroke="#a3b1c6" strokeWidth={1.2} />
              <LabelList dataKey="rate" position="top" offset={14} formatter={(v) => formatPercent(Number(v))}
                style={{ fill: "#f1f5f9", fontSize: 12, fontWeight: 600 }} />
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
      <figcaption className="mt-2 text-xs text-ink-3">
        Each test scored by a model that never saw it. Error bars: 95% Wilson interval.
      </figcaption>
    </figure>
  );
}
