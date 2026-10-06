"use client";

import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";

import { ChartTooltip } from "@/components/charts/chart-tooltip";
import { OUTCOME_COLORS, OUTCOME_LABEL, type Outcome } from "@/lib/chart-theme";
import { formatPercent } from "@/lib/format";
import type { StatsResponse } from "@/lib/types";

/** Observed outcome mix of all FLEX tests, with direct labels (legend + counts) beside the ring. */
export function OutcomeDonut({ stats }: { stats: StatsResponse }) {
  const e = stats.experiments;
  const data: { name: Outcome; value: number }[] = [
    { name: "Extinction", value: e.extinction },
    { name: "Completion", value: e.completion },
    { name: "Disruption", value: e.disruption },
  ];
  return (
    <figure className="flex flex-col items-center gap-5 2xl:flex-row" aria-label={`Outcomes of ${e.total} FLEX tests`}>
      <div className="relative h-44 w-44 shrink-0">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie data={data} dataKey="value" nameKey="name" innerRadius="68%" outerRadius="100%" paddingAngle={2}
              stroke="#0b1020" strokeWidth={2} startAngle={90} endAngle={-270} isAnimationActive>
              {data.map((d) => <Cell key={d.name} fill={OUTCOME_COLORS[d.name]} />)}
            </Pie>
            <Tooltip
              content={({ active, payload }) => {
                if (!active || !payload?.length) return null;
                const p = payload[0];
                const name = p.name as Outcome;
                return <ChartTooltip title={OUTCOME_LABEL[name]} rows={[
                  { label: "Tests", value: String(p.value), color: OUTCOME_COLORS[name] },
                  { label: "Share", value: formatPercent(Number(p.value) / e.total, 1) },
                ]} />;
              }}
            />
          </PieChart>
        </ResponsiveContainer>
        <div className="pointer-events-none absolute inset-0 grid place-items-center text-center">
          <div>
            <p className="font-display text-3xl font-semibold tabular-nums">{e.total}</p>
            <p className="label-caps">tests</p>
          </div>
        </div>
      </div>
      <figcaption className="w-full space-y-2.5">
        {data.map((d) => (
          <div key={d.name} className="flex items-center justify-between gap-3 text-sm">
            <span className="flex items-center gap-2 text-ink-2">
              <span className="size-2.5 rounded-sm" style={{ background: OUTCOME_COLORS[d.name] }} aria-hidden="true" />
              {OUTCOME_LABEL[d.name]}
            </span>
            <span className="font-mono tabular-nums text-ink">
              {d.value} <span className="text-ink-3">· {formatPercent(d.value / e.total)}</span>
            </span>
          </div>
        ))}
        <p className="pt-1 text-xs text-ink-3">
          Completion and disruption count as <span className="text-ink-2">sustained combustion</span> ({e.sustained} tests).
        </p>
      </figcaption>
    </figure>
  );
}
