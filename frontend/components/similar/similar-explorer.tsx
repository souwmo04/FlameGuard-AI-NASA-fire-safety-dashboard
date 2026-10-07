"use client";

import { ArrowUpRight, History, Info, TriangleAlert } from "lucide-react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useState } from "react";
import useSWR from "swr";

import { OutcomeShape } from "@/components/charts/outcome-shape";
import { Panel } from "@/components/dashboard/panel";
import { Segmented } from "@/components/risk/segmented";
import { ConditionsFields } from "@/components/scenario/conditions-fields";
import { PageHeader } from "@/components/ui/page-header";
import { ProvenanceBadge } from "@/components/ui/provenance-badge";
import { RiskBadge } from "@/components/ui/risk-badge";
import { ErrorState, LoadingState } from "@/components/ui/states";
import { useApi } from "@/hooks/use-api";
import { useDebouncedValue } from "@/hooks/use-debounced-value";
import { usePredict } from "@/hooks/use-predict";
import { api, endpoints, type ApiError } from "@/lib/api";
import { OUTCOME_SHORT, type Outcome } from "@/lib/chart-theme";
import { cn } from "@/lib/cn";
import { formatPercent, formatRisk } from "@/lib/format";
import { REFERENCE_SCENARIO, useLastAnalysis } from "@/lib/last-analysis";
import { conditionsFromQuery, conditionsToQuery } from "@/lib/scenario-url";
import type { Conditions, DomainResponse, SimilarResponse } from "@/lib/types";

import { Constellation } from "./constellation";
import { SimilarList } from "./similar-list";

type K = "3" | "5" | "8" | "12";
const OUTCOMES: Outcome[] = ["Extinction", "Completion", "Disruption"];
/** Below this similarity the nearest test is more than one typical spacing away (see the method note). */
const FAR = 37;

export function SimilarExplorer() {
  const domain = useApi<DomainResponse>(endpoints.domain);
  const params = useSearchParams();
  const last = useLastAnalysis();
  const [linked] = useState(() => conditionsFromQuery(params));
  const [form, setForm] = useState<Conditions>(linked ?? REFERENCE_SCENARIO);
  const [k, setK] = useState<K>("8");
  const [hovered, setHovered] = useState<number | null>(null);

  const q = useDebouncedValue(form);
  const similar = useSWR<SimilarResponse, ApiError>(
    ["similar", JSON.stringify(q), k],
    () => api.similar({ ...q, k: Number(k) }),
    { revalidateOnFocus: false, shouldRetryOnError: false, keepPreviousData: true },
  );
  const prediction = usePredict(q);
  const busy = similar.isValidating || q !== form;

  const data = similar.data;
  const items = data?.items ?? [];
  const kept = items.filter((i) => i.experiment.sustained).length;
  const weight = items.reduce((s, i) => s + i.similarity, 0);
  const weighted = weight > 0 ? items.reduce((s, i) => s + (i.experiment.sustained ? i.similarity : 0), 0) / weight : 0;
  const nearest = items[0]?.similarity ?? 0;
  const p = prediction.data?.sustained_probability;
  const gap = p !== undefined ? Math.abs(p - weighted) : null;

  return (
    <div className="space-y-6 lg:space-y-8">
      <PageHeader
        eyebrow="Similar Tests"
        title="Similar NASA Tests"
        subtitle="Describe a burning droplet and find the real ISS tests that came closest — then see what actually happened to them."
      />

      {domain.error && <ErrorState message={domain.error.message} onRetry={() => domain.mutate()} />}

      <div className="grid gap-4 xl:grid-cols-[minmax(0,4fr)_minmax(0,8fr)] xl:gap-6">
        <Panel title="Your conditions" provenance="hypothetical" description="Results update as you change them." delay={0.05}
          className="xl:sticky xl:top-20 xl:self-start">
          {domain.data ? (
            <div className="grid gap-5 md:grid-cols-2 md:gap-x-8 xl:grid-cols-1">
              <ConditionsFields value={form} onChange={setForm} domain={domain.data} />
              <Segmented<K> label="Tests to show" value={k} onChange={setK}
                options={[{ value: "3", label: "3" }, { value: "5", label: "5" }, { value: "8", label: "8" }, { value: "12", label: "12" }]} />
              <div className="flex flex-wrap gap-2 md:col-span-2 xl:col-span-1">
                {last && (
                  <button type="button" onClick={() => setForm(last)}
                    className="inline-flex items-center gap-1.5 rounded-lg border border-white/10 px-3 py-1.5 text-xs text-ink-2 transition hover:border-white/20 hover:text-ink">
                    <History className="size-3.5 text-plasma" aria-hidden="true" />Use my last analysis
                  </button>
                )}
                <Link href={`/risk?${conditionsToQuery(form)}`}
                  className="inline-flex items-center gap-1.5 rounded-lg border border-white/10 px-3 py-1.5 text-xs text-ink-2 transition hover:border-white/20 hover:text-ink">
                  <ArrowUpRight className="size-3.5 text-flame" aria-hidden="true" />Full Fire Risk analysis
                </Link>
              </div>
            </div>
          ) : (
            <LoadingState rows={6} label="Loading tested ranges" />
          )}
        </Panel>

        <div className={cn("min-w-0 space-y-4 transition-opacity xl:space-y-6", busy && data && "opacity-75")}>
          {similar.error ? (
            <ErrorState message={similar.error.message} onRetry={() => similar.mutate()} />
          ) : !data ? (
            <Panel title="Nearest tests" provenance="observed"><LoadingState rows={8} label="Searching NASA tests" /></Panel>
          ) : (
            <>
              <Panel title="Evidence check" provenance="observed"
                description={`What happened in the ${items.length} nearest tests, next to what the model predicts.`} delay={0.05}>
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2 rounded-xl border border-prov-observed/25 bg-prov-observed/[0.05] p-4">
                    <ProvenanceBadge kind="observed" compact />
                    <p className="font-display text-3xl font-bold tabular-nums text-ink">
                      {kept} <span className="text-lg font-medium text-ink-3">of {items.length} kept burning</span>
                    </p>
                    <div className="flex flex-wrap gap-x-3 gap-y-1 text-xs text-ink-3">
                      {OUTCOMES.map((o) => {
                        const n = items.filter((i) => i.experiment.outcome === o).length;
                        return n > 0 && <span key={o} className="flex items-center gap-1.5"><OutcomeShape outcome={o} />{OUTCOME_SHORT[o]} {n}</span>;
                      })}
                    </div>
                    <p className="text-xs text-ink-3">Weighted by similarity: <span className="font-mono text-ink-2">{formatPercent(weighted)}</span> kept burning.</p>
                  </div>
                  <div className="space-y-2 rounded-xl border border-prov-prediction/25 bg-prov-prediction/[0.05] p-4">
                    <ProvenanceBadge kind="prediction" compact />
                    {prediction.data ? (
                      <>
                        <div className="flex flex-wrap items-center gap-3">
                          <p className="font-display text-3xl font-bold tabular-nums text-ink">{formatRisk(prediction.data.fire_risk)}</p>
                          <RiskBadge level={prediction.data.risk_level} />
                        </div>
                        <p className="text-xs text-ink-3">Model: {formatPercent(prediction.data.sustained_probability)} chance this droplet keeps burning.</p>
                      </>
                    ) : prediction.error ? (
                      <p className="text-xs text-risk-high">{prediction.error.message}</p>
                    ) : (
                      <LoadingState rows={2} label="Predicting" />
                    )}
                  </div>
                </div>
                <div className="mt-4 space-y-2">
                  {nearest < FAR && (
                    <p role="alert" className="flex gap-2 rounded-lg border border-risk-elevated/30 bg-risk-elevated/[0.06] p-3 text-xs text-ink-2">
                      <TriangleAlert className="mt-0.5 size-3.5 shrink-0 text-risk-elevated" aria-hidden="true" />
                      The closest NASA test is only {Math.round(nearest)}% similar — no tested condition is near these settings, so neither the tests nor the model say much here.
                    </p>
                  )}
                  {gap !== null && (
                    <p className="flex gap-2 text-xs text-ink-3">
                      <Info className="mt-0.5 size-3.5 shrink-0" aria-hidden="true" />
                      {gap < 0.2
                        ? "The nearby tests and the model broadly agree."
                        : "The nearby tests and the model differ noticeably — worth opening the individual tests."}{" "}
                      A handful of neighbouring tests is a sanity check, not a validation: they differ in droplet size and atmosphere, and the model was trained on them.
                    </p>
                  )}
                </div>
              </Panel>

              <div className="grid gap-4 lg:grid-cols-2 xl:gap-6">
                <Panel title="Distance map" provenance="observed" description="Closer to the centre = more similar. Select a marker to open the test." delay={0.1}
                  className="lg:sticky lg:top-20 lg:self-start">
                  <Constellation items={items} radius={data.support_radius} hovered={hovered} onHover={setHovered} />
                  <div className="mt-2 flex flex-wrap justify-center gap-x-4 gap-y-1 text-xs text-ink-3">
                    {OUTCOMES.map((o) => <span key={o} className="flex items-center gap-1.5"><OutcomeShape outcome={o} />{OUTCOME_SHORT[o]}</span>)}
                  </div>
                </Panel>
                <Panel title="Nearest tests" provenance="observed" description="Chips show how each test differs from your conditions." delay={0.15}>
                  <SimilarList items={items} query={data.query} hovered={hovered} onHover={setHovered} />
                </Panel>
              </div>

              <p className="flex gap-2 text-xs leading-relaxed text-ink-3">
                <Info className="mt-0.5 size-3.5 shrink-0" aria-hidden="true" />{data.method}
              </p>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
