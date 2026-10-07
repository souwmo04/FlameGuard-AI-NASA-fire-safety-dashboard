"use client";

import { signed, Waterfall, type WaterfallRow } from "@/components/charts/waterfall";
import { formatRisk } from "@/lib/format";
import type { WhatIfResponse } from "@/lib/types";

import { SCENARIO } from "./scenario-style";

const STEP_LABEL: Record<string, string> = {
  oxygen: "Oxygen",
  suppressant: "Suppressant",
  "droplet size": "Droplet size",
  fuel: "Fuel",
};

const EXTRAPOLATION = "This intermediate state is far from any tested FLEX condition (extrapolation).";

/** A → B one input at a time: A's score, each change as a floating bar, then B's score. */
export function PathWaterfall({ data, alert }: { data: WhatIfResponse; alert: number }) {
  const [first, ...steps] = data.path;
  const rows: WaterfallRow[] = [
    { key: "a", label: `Scenario A`, from: 0, to: first.fire_risk, value: formatRisk(first.fire_risk), kind: "total",
      barClass: SCENARIO.a.bar, valueClass: SCENARIO.a.text, emphasis: true,
      sr: `Scenario A: Fire Risk ${first.fire_risk.toFixed(1)}.` },
  ];
  let prev = first.fire_risk;
  for (const s of steps) {
    const kind = Math.abs(s.delta) < 0.5 ? "neutral" : s.delta > 0 ? "raises" : "lowers";
    rows.push({
      key: s.step, label: STEP_LABEL[s.step] ?? s.step, detail: s.change, from: prev, to: s.fire_risk,
      value: signed(s.delta), kind, warning: s.supported ? undefined : EXTRAPOLATION,
      sr: `Changing ${s.change} moves Fire Risk by ${signed(s.delta)} points, to ${s.fire_risk.toFixed(1)}.`,
    });
    prev = s.fire_risk;
  }
  rows.push({ key: "b", label: "Scenario B", from: 0, to: data.b.fire_risk, value: formatRisk(data.b.fire_risk), kind: "total",
    barClass: SCENARIO.b.bar, valueClass: SCENARIO.b.text, emphasis: true,
    sr: `Scenario B: Fire Risk ${data.b.fire_risk.toFixed(1)}.` });

  return <Waterfall rows={rows} alert={alert} labelWidth="15rem" />;
}
