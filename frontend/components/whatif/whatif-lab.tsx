"use client";

import { ArrowDown, ArrowLeftRight, Copy, Droplet, FlaskConical, History, Info, Repeat, Wind, type LucideIcon } from "lucide-react";
import { useSearchParams } from "next/navigation";
import { useState } from "react";

import { Panel } from "@/components/dashboard/panel";
import { Segmented } from "@/components/risk/segmented";
import { clamp, ConditionsFields, withFuel, withSuppressant } from "@/components/scenario/conditions-fields";
import { GlassCard } from "@/components/ui/glass-card";
import { PageHeader } from "@/components/ui/page-header";
import { ErrorState, LoadingState } from "@/components/ui/states";
import { useApi } from "@/hooks/use-api";
import { useDebouncedValue } from "@/hooks/use-debounced-value";
import { useWhatIf, type SweepFeature } from "@/hooks/use-what-if";
import { endpoints } from "@/lib/api";
import { cn } from "@/lib/cn";
import { REFERENCE_SCENARIO, useLastAnalysis } from "@/lib/last-analysis";
import { conditionsFromQuery } from "@/lib/scenario-url";
import type { Conditions, DomainResponse, ExperimentList, Fuel, StatsResponse } from "@/lib/types";

import { ComparisonHero } from "./comparison-hero";
import { PathWaterfall } from "./path-waterfall";
import { SCENARIO, type ScenarioKey } from "./scenario-style";
import { ScenarioTag } from "./scenario-tag";
import { comparableTests, SweepChart } from "./sweep-chart";

interface Preset {
  id: string;
  label: string;
  icon: LucideIcon;
  apply: (a: Conditions, d: DomainResponse) => Conditions;
}

const ranges = (c: Conditions, d: DomainResponse) => d.fuels[c.fuel as Fuel];

/** One-click changes: B becomes A with a single input altered (kept inside the tested ranges). */
const PRESETS: Preset[] = [
  { id: "fuel", label: "Switch fuel", icon: Repeat, apply: (a, d) => withFuel(a, a.fuel === "Methanol" ? "Heptane" : "Methanol", d) },
  { id: "o2", label: "Lower O₂ by 4 points", icon: ArrowDown,
    apply: (a, d) => ({ ...a, oxygen_percent: clamp(a.oxygen_percent - 4, ranges(a, d).oxygen_percent) }) },
  { id: "co2", label: "Add 15% CO₂", icon: FlaskConical, apply: (a, d) => ({ ...withSuppressant(a, "CO2", d), suppressant_percent: 15 }) },
  { id: "he", label: "Add 15% helium", icon: Wind, apply: (a, d) => ({ ...withSuppressant(a, "He", d), suppressant_percent: 15 }) },
  { id: "drop", label: "Droplet +1 mm", icon: Droplet,
    apply: (a, d) => ({ ...a, droplet_diameter_mm: clamp(a.droplet_diameter_mm + 1, ranges(a, d).droplet_diameter_mm) }) },
];

const DEFAULT_B: Conditions = { ...REFERENCE_SCENARIO, fuel: "Heptane" };

const chip = "inline-flex items-center gap-1.5 rounded-lg border border-white/10 bg-white/[0.03] px-3 py-1.5 text-xs font-medium text-ink-2 transition hover:border-white/20 hover:bg-white/[0.06] hover:text-ink";

export function WhatIfLab() {
  const domain = useApi<DomainResponse>(endpoints.domain);
  const stats = useApi<StatsResponse>(endpoints.stats);
  const tests = useApi<ExperimentList>(`${endpoints.experiments}?limit=300`);
  const last = useLastAnalysis();

  // Linked conditions (?fuel=…&o2=…) become scenario A, with B starting as a copy to modify.
  const params = useSearchParams();
  const [linked] = useState(() => conditionsFromQuery(params));
  const [a, setA] = useState<Conditions>(linked ?? REFERENCE_SCENARIO);
  const [b, setB] = useState<Conditions>(linked ?? DEFAULT_B);
  const [feature, setFeature] = useState<SweepFeature>("oxygen");
  const [observedFor, setObservedFor] = useState<ScenarioKey | "off">("a");

  const da = useDebouncedValue(a);
  const db = useDebouncedValue(b);
  const result = useWhatIf(da, db, feature);
  const data = result.data;
  const busy = result.isValidating || da !== a || db !== b;
  const alert = stats.data?.model.alert_threshold_score ?? 18.4;

  const observedConditions = observedFor === "a" ? da : observedFor === "b" ? db : null;
  const observed = observedConditions && tests.data ? comparableTests(tests.data.items.filter((e) => e.in_model_scope), observedConditions, feature) : [];

  const editor = (which: ScenarioKey, value: Conditions, onChange: (c: Conditions) => void) => (
    <Panel
      title={`Scenario ${SCENARIO[which].letter}`}
      provenance="hypothetical"
      description={which === "a" ? "The starting point." : "The conditions you want to compare."}
      actions={<ScenarioTag which={which} />}
      delay={which === "a" ? 0.05 : 0.1}
      className={which === "a" ? "order-1" : "order-2 xl:order-3"}
    >
      {domain.data ? (
        <div className="grid gap-5">
          <ConditionsFields value={value} onChange={onChange} domain={domain.data} accent={SCENARIO[which].accent} />
        </div>
      ) : (
        <LoadingState rows={6} label="Loading tested ranges" />
      )}
    </Panel>
  );

  return (
    <div className="space-y-6 lg:space-y-8">
      <PageHeader
        eyebrow="What-If Lab"
        title="What-If Lab"
        subtitle="Change one condition at a time and watch the model respond — then check the answer against what NASA actually observed."
      />

      {domain.error && <ErrorState message={domain.error.message} onRetry={() => domain.mutate()} />}

      {/* quick changes */}
      <GlassCard className="flex flex-col gap-3 p-4 sm:p-5 lg:flex-row lg:items-center lg:justify-between">
        <div className="flex flex-wrap items-center gap-2">
          <span className="label-caps mr-1">Make B = A, then</span>
          {PRESETS.map((p) => {
            const Icon = p.icon;
            return (
              <button key={p.id} type="button" className={chip} disabled={!domain.data}
                onClick={() => domain.data && setB(p.apply(a, domain.data))}>
                <Icon className="size-3.5 text-flame" aria-hidden="true" />{p.label}
              </button>
            );
          })}
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <button type="button" className={chip} onClick={() => { setA(b); setB(a); }}>
            <ArrowLeftRight className="size-3.5" aria-hidden="true" />Swap A and B
          </button>
          <button type="button" className={chip} onClick={() => setB(a)}>
            <Copy className="size-3.5" aria-hidden="true" />Copy A to B
          </button>
          {last && (
            <button type="button" className={chip} onClick={() => setA(last)}>
              <History className="size-3.5 text-plasma" aria-hidden="true" />Use my last Fire Risk analysis as A
            </button>
          )}
        </div>
      </GlassCard>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-[minmax(0,1fr)_minmax(0,1.15fr)_minmax(0,1fr)] xl:gap-6">
        {editor("a", a, setA)}
        <div className="order-3 md:col-span-2 xl:order-2 xl:col-span-1">
          {result.error ? (
            <ErrorState message={result.error.message} onRetry={() => result.mutate()} />
          ) : data ? (
            <ComparisonHero data={data} busy={busy} />
          ) : (
            <GlassCard className="p-6"><LoadingState rows={6} label="Comparing scenarios" /></GlassCard>
          )}
        </div>
        {editor("b", b, setB)}
      </div>

      {data && (
        <div className="grid gap-4 xl:grid-cols-[minmax(0,7fr)_minmax(0,5fr)] xl:gap-6">
          <Panel
            title={`Fire Risk as ${feature === "oxygen" ? "oxygen" : "droplet size"} varies`}
            provenance="prediction"
            description="Everything else held at each scenario's settings. NASA tests overlaid for a reality check."
            delay={0.05}
          >
            <div className="space-y-4">
              <div className="grid gap-4 sm:grid-cols-2">
                <Segmented<SweepFeature> label="Vary" value={feature} onChange={setFeature}
                  options={[{ value: "oxygen", label: "Oxygen" }, { value: "droplet", label: "Droplet size" }]} />
                <Segmented<ScenarioKey | "off"> label="Show NASA tests like" value={observedFor} onChange={setObservedFor}
                  options={[{ value: "a", label: "A" }, { value: "b", label: "B" }, { value: "off", label: "Off" }]} />
              </div>
              {data.sweep && (
                <div className={cn("transition-opacity", busy && "opacity-70")}>
                  <SweepChart sweep={data.sweep} a={data.a.conditions} b={data.b.conditions} aRisk={data.a.fire_risk}
                    bRisk={data.b.fire_risk} alert={alert} observed={observed} observedFor={observedFor === "off" ? null : observedFor} />
                </div>
              )}
            </div>
          </Panel>

          <Panel title="From A to B, one change at a time" provenance="prediction"
            description="Oxygen, then suppressant, droplet size and fuel." delay={0.12}>
            {data.path.length > 1 ? (
              <PathWaterfall key={JSON.stringify([data.a.conditions, data.b.conditions])} data={data} alert={alert} />
            ) : (
              <p className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-4 text-sm text-ink-3">
                A and B are identical. Change a condition in B, or use one of the quick changes above.
              </p>
            )}
          </Panel>
        </div>
      )}

      {data && (
        <Panel title="Read before you conclude" provenance="hypothetical" delay={0.05}>
          <ul className="space-y-2.5">
            {[...data.notes, "Both scenarios are hypothetical. Fire Risk values are model predictions trained on NASA FLEX droplet tests, not NASA measurements and not a certified spacecraft fire-safety assessment."].map((n) => (
              <li key={n} className="flex gap-2.5 text-sm text-ink-2">
                <Info className="mt-0.5 size-4 shrink-0 text-prov-hypothetical" aria-hidden="true" />{n}
              </li>
            ))}
          </ul>
        </Panel>
      )}
    </div>
  );
}
