"use client";

import { Info, Scale, TriangleAlert } from "lucide-react";
import { useState } from "react";

import { Panel } from "@/components/dashboard/panel";
import { Segmented } from "@/components/risk/segmented";
import { GlassCard } from "@/components/ui/glass-card";
import { PageHeader } from "@/components/ui/page-header";
import { ProvenanceBadge } from "@/components/ui/provenance-badge";
import { ErrorState, LoadingState } from "@/components/ui/states";
import { useApi } from "@/hooks/use-api";
import { endpoints } from "@/lib/api";
import type { SuppressantsResponse } from "@/lib/types";

import { DesignScatter } from "./design-scatter";
import { O2Forest } from "./o2-forest";

type FuelKey = "Methanol" | "Heptane";
type PressureKey = "1atm" | "0.7atm";

function Stat({ value, label }: { value: string; label: string }) {
  return (
    <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-3.5">
      <p className="font-display text-2xl font-bold tabular-nums text-ink">{value}</p>
      <p className="text-xs text-ink-3">{label}</p>
    </div>
  );
}

export function SuppressantLab() {
  const res = useApi<SuppressantsResponse>(endpoints.suppressants);
  const [fuel, setFuel] = useState<FuelKey>("Heptane");
  const [pressure, setPressure] = useState<PressureKey>("1atm");
  const [supp, setSupp] = useState<"CO2" | "He">("CO2");

  const header = (
    <PageHeader
      eyebrow="Suppressant Lab"
      title="Suppressant Lab"
      subtitle="Nitrogen, CO₂ and helium compared using observed ISS tests only — no machine-learning model — and an honest verdict on what the data supports."
    />
  );
  if (res.error) return <div className="space-y-6">{header}<ErrorState message={res.error.message} onRetry={() => res.mutate()} /></div>;
  if (!res.data) return <div className="space-y-6">{header}<LoadingState rows={10} label="Loading suppressant analysis" /></div>;

  const d = res.data;
  const estimable = d.estimates.filter((e) => e.estimable).length;
  const allOverlap = d.comparisons.length > 0 && d.comparisons.every((c) => c.intervals_overlap);
  const scatterEstimate = d.estimates.find((e) => e.fuel === fuel && e.pressure_level === pressure && e.suppressant === supp);

  return (
    <div className="space-y-6 lg:space-y-8">
      {header}

      <GlassCard glow className="p-5 sm:p-7">
        <div className="grid gap-6 lg:grid-cols-[minmax(0,1.4fr)_minmax(0,1fr)] lg:items-center">
          <div className="space-y-3">
            <div className="flex flex-wrap items-center gap-2">
              <span className="label-caps text-flame">Verdict</span>
              <ProvenanceBadge kind="estimate" compact />
            </div>
            <h2 className="flex items-start gap-3 font-display text-2xl font-bold tracking-tight text-ink sm:text-3xl">
              <Scale className="mt-1 size-7 shrink-0 text-flame" aria-hidden="true" />
              {allOverlap ? "The NASA data cannot rank these suppressants." : "Some suppressant series differ."}
            </h2>
            <p className="text-sm leading-relaxed text-ink-2">{d.conclusion}</p>
          </div>
          <div className="grid grid-cols-3 gap-3">
            <Stat value={String(d.estimates.length)} label="fuel × pressure × gas series" />
            <Stat value={String(estimable)} label="with enough tests to estimate" />
            <Stat value={String(d.comparisons.length)} label={`like-for-like comparison${d.comparisons.length === 1 ? "" : "s"} possible`} />
          </div>
        </div>
      </GlassCard>

      <div className="grid gap-4 xl:grid-cols-[minmax(0,7fr)_minmax(0,5fr)] xl:gap-6">
        <Panel title="Oxygen needed to keep half the droplets burning (O₂₅₀)" provenance="estimate"
          description="Per series of observed tests, for a 3 mm droplet. Compare rows within a box only." delay={0.05}>
          <O2Forest estimates={d.estimates} />
        </Panel>

        <div className="space-y-4 xl:space-y-6">
          <Panel title="How to read O₂₅₀" delay={0.1}>
            <div className="space-y-2.5 text-sm leading-relaxed text-ink-2">
              <p>O₂₅₀ is the oxygen level at which, in a given test series, a droplet was as likely to keep burning as to go out.</p>
              <p>A <span className="text-ink">higher</span> O₂₅₀ means the flame needed <span className="text-ink">more oxygen</span> to survive in that atmosphere — the mixture was harder to burn in.</p>
              <p>Two series differ only if their 95% intervals do <span className="text-ink">not</span> overlap.</p>
            </div>
          </Panel>
          <Panel title="Like-for-like comparisons" provenance="estimate" delay={0.15}>
            <ul className="space-y-3">
              {d.comparisons.map((c) => (
                <li key={`${c.fuel}-${c.pressure_level}`} className="space-y-2 rounded-xl border border-white/[0.06] bg-white/[0.02] p-3.5">
                  <span className={c.intervals_overlap
                    ? "inline-flex rounded-full border border-risk-elevated/40 bg-risk-elevated/10 px-2.5 py-0.5 text-[0.6875rem] font-semibold uppercase tracking-[0.12em] text-risk-elevated"
                    : "inline-flex rounded-full border border-risk-low/40 bg-risk-low/10 px-2.5 py-0.5 text-[0.6875rem] font-semibold uppercase tracking-[0.12em] text-risk-low"}>
                    {c.intervals_overlap ? "Intervals overlap — no ranking" : "Intervals separate"}
                  </span>
                  <p className="text-sm text-ink-2">{c.statement}</p>
                </li>
              ))}
              {d.comparisons.length === 0 && <li className="text-sm text-ink-3">No fuel and pressure has more than one estimable series.</li>}
            </ul>
          </Panel>
        </div>
      </div>

      <Panel title="How the suppressants were actually tested" provenance="observed"
        description="Every ISS test in one series. More suppressant always came with less oxygen, so the two effects are confounded." delay={0.05}>
        <div className="space-y-5">
          <div className="grid gap-4 md:grid-cols-3">
            <Segmented<FuelKey> label="Fuel" value={fuel} onChange={setFuel}
              options={[{ value: "Methanol", label: "Methanol" }, { value: "Heptane", label: "n-Heptane" }]} />
            <Segmented<PressureKey> label="Pressure" value={pressure} onChange={setPressure}
              options={[{ value: "1atm", label: "1 atm" }, { value: "0.7atm", label: "0.7 atm" }]} />
            <Segmented<"CO2" | "He"> label="Suppressant" value={supp} onChange={setSupp}
              options={[{ value: "CO2", label: "CO₂" }, { value: "He", label: "Helium" }]} />
          </div>
          <DesignScatter observed={d.observed} fuel={fuel} pressure={pressure} suppressant={supp} estimate={scatterEstimate} />
        </div>
      </Panel>

      <Panel title="Caveats" provenance="estimate" delay={0.05}>
        <ul className="space-y-2.5">
          {d.caveats.map((c) => (
            <li key={c} className="flex gap-2.5 text-sm text-ink-2">
              <TriangleAlert className="mt-0.5 size-4 shrink-0 text-risk-elevated" aria-hidden="true" />{c}
            </li>
          ))}
          <li className="flex gap-2.5 text-sm text-ink-3">
            <Info className="mt-0.5 size-4 shrink-0" aria-hidden="true" />{d.method}
          </li>
        </ul>
      </Panel>
    </div>
  );
}
