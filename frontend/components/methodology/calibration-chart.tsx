"use client";

import { CartesianGrid, ComposedChart, ErrorBar, Line, ResponsiveContainer, Scatter, Tooltip, XAxis, YAxis, ZAxis } from "recharts";

import { ChartTooltip } from "@/components/charts/chart-tooltip";
import { AXIS, GRID } from "@/lib/chart-theme";
import { formatPercent } from "@/lib/format";
import type { ModelInfoResponse } from "@/lib/types";

/** Reliability diagram: predicted vs observed share of sustained tests per bin, 95% Wilson intervals, ideal diagonal. */
export function CalibrationChart({ bins }: { bins: ModelInfoResponse["calibration"] }) {
  const points = bins.map((b) => ({
    x: b.mean_predicted * 100,
    y: b.observed_rate * 100,
    err: [Math.max(0, (b.observed_rate - b.ci_low) * 100), Math.max(0, (b.ci_high - b.observed_rate) * 100)],
    tests: b.tests,
    lo: b.ci_low,
    hi: b.ci_high,
  }));
  return (
    <figure aria-label="Calibration: predicted versus observed share of tests that kept burning, per bin of out-of-fold predictions" className="space-y-2">
      <div className="h-72 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart margin={{ top: 10, right: 12, bottom: 22, left: -6 }}>
            <CartesianGrid {...GRID} />
            <XAxis type="number" dataKey="x" domain={[0, 100]} ticks={[0, 25, 50, 75, 100]} unit="%" {...AXIS}
              label={{ value: "Predicted chance of sustained burning", position: "insideBottom", offset: -12, fill: "#7b8aa3", fontSize: 11 }} />
            <YAxis type="number" dataKey="y" domain={[0, 100]} ticks={[0, 25, 50, 75, 100]} unit="%" {...AXIS} />
            <ZAxis range={[70, 70]} />
            <Line data={[{ x: 0, y: 0 }, { x: 100, y: 100 }]} dataKey="y" stroke="#7b8aa3" strokeDasharray="5 5" dot={false} activeDot={false} isAnimationActive={false} />
            <Scatter data={points} fill="#cbd5e1" stroke="#05070d" strokeWidth={1.5} isAnimationActive={false}>
              <ErrorBar dataKey="err" direction="y" width={5} stroke="#94a3b8" strokeWidth={1.2} />
            </Scatter>
            <Tooltip
              cursor={false}
              content={({ active, payload }) => {
                const p = payload?.find((x) => x.payload && "tests" in x.payload)?.payload as (typeof points)[number] | undefined;
                if (!active || !p) return null;
                return <ChartTooltip title={`${p.tests} tests`} rows={[
                  { label: "Predicted", value: `${p.x.toFixed(1)}%` },
                  { label: "Observed", value: formatPercent(p.y / 100) },
                  { label: "95% CI", value: `${formatPercent(p.lo)}–${formatPercent(p.hi)}` },
                ]} />;
              }}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
      <figcaption className="text-xs text-ink-3">
        Points on the dashed diagonal would mean perfect calibration. Bars show 95% Wilson intervals; each bin holds about 30 out-of-fold predictions.
      </figcaption>
    </figure>
  );
}
