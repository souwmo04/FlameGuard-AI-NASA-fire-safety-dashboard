"use client";

import { Info, Loader2, Radar, RefreshCw, Zap } from "lucide-react";
import { useSearchParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import useSWR from "swr";

import { Panel } from "@/components/dashboard/panel";
import { ConditionsFields } from "@/components/scenario/conditions-fields";
import { PageHeader } from "@/components/ui/page-header";
import { ProvenanceBadge } from "@/components/ui/provenance-badge";
import { RiskBadge } from "@/components/ui/risk-badge";
import { EmptyState, ErrorState, LoadingState } from "@/components/ui/states";
import { useApi } from "@/hooks/use-api";
import { usePredict } from "@/hooks/use-predict";
import { api, endpoints, type ApiError } from "@/lib/api";
import { cn } from "@/lib/cn";
import { describeConditions } from "@/lib/conditions";
import { REFERENCE_SCENARIO, saveLastAnalysis } from "@/lib/last-analysis";
import { conditionsFromQuery } from "@/lib/scenario-url";
import type { Conditions, DomainResponse, Fuel, ModelInfoResponse, SimilarResponse, StatsResponse } from "@/lib/types";

import { ContributionWaterfall } from "./contribution-waterfall";
import { EvidencePanel } from "./evidence-panel";
import { InterpretationCard } from "./interpretation-card";
import { NearestTests } from "./nearest-tests";
import { ProbabilityBars } from "./probability-bars";
import { RiskGauge } from "./risk-gauge";

const same = (a: Conditions, b: Conditions) => JSON.stringify(a) === JSON.stringify(b);

export function FireRiskAnalyzer() {
  const domain = useApi<DomainResponse>(endpoints.domain);
  const stats = useApi<StatsResponse>(endpoints.stats);
  const model = useApi<ModelInfoResponse>(endpoints.model);
  // Linked conditions (?fuel=…&o2=…) pre-fill the form and are analysed straight away.
  const params = useSearchParams();
  const [linked] = useState(() => conditionsFromQuery(params));
  const [form, setForm] = useState<Conditions>(linked ?? REFERENCE_SCENARIO);
  const [submitted, setSubmitted] = useState<Conditions | null>(linked);

  const prediction = usePredict(submitted);
  const similar = useSWR<SimilarResponse, ApiError>(
    submitted ? ["similar", JSON.stringify(submitted)] : null,
    () => api.similar({ ...(submitted as Conditions), k: 3 }),
    { revalidateOnFocus: false, shouldRetryOnError: false, keepPreviousData: true },
  );

  // Persist each successful analysis for Mission Control (external storage write, no React state).
  useEffect(() => {
    if (prediction.data) saveLastAnalysis(prediction.data.conditions);
  }, [prediction.data]);

  const ranges = domain.data?.fuels[form.fuel as Fuel];
  const stale = !!submitted && !!prediction.data && !same(form, submitted);
  const alert = stats.data?.model.alert_threshold_score ?? 18.4;
  const result = prediction.data;

  const analyze = () => setSubmitted({ ...form });

  const notInputs = useMemo(
    () => [
      ["Pressure", "Valid for 0.7–1 atm only; dropped as an input (decision D-001)."],
      ["Temperature", "FLEX burned droplets at ambient temperature; not recorded."],
      ["Airflow", "FLEX chambers were quiescent; airflow was not a test variable."],
    ],
    [],
  );

  return (
    <div className="space-y-6 lg:space-y-8">
      <PageHeader
        eyebrow="Fire Risk"
        title="Fire Risk Analysis"
        subtitle="Set the conditions of a burning fuel droplet and see whether the model expects it to keep burning — with the evidence behind the number."
      />

      {(domain.error || stats.error) && <ErrorState message={(domain.error ?? stats.error)!.message} onRetry={() => { domain.mutate(); stats.mutate(); }} />}

      <div className="grid gap-4 xl:grid-cols-[minmax(0,5fr)_minmax(0,7fr)] xl:gap-6">
        {/* conditions */}
        <Panel title="Experiment conditions" provenance="hypothetical" description="Limited to the ranges tested in NASA FLEX." delay={0.05}>
          {!ranges ? (
            <LoadingState rows={8} label="Loading tested ranges" />
          ) : (
            <form
              className="grid gap-6 md:grid-cols-2 md:gap-x-8 xl:grid-cols-1"
              onSubmit={(e) => {
                e.preventDefault();
                analyze();
              }}
            >
              <ConditionsFields value={form} onChange={setForm} domain={domain.data!} />

              <details className="group rounded-xl md:col-span-2 xl:col-span-1 border border-white/[0.06] bg-white/[0.02] p-3.5 text-sm">
                <summary className="flex cursor-pointer list-none items-center gap-2 text-ink-2">
                  <Info className="size-4 text-plasma" aria-hidden="true" /> Why no pressure, temperature or airflow?
                </summary>
                <dl className="mt-3 space-y-2 text-xs">
                  {notInputs.map(([k, v]) => (
                    <div key={k}><dt className="inline font-semibold text-ink">{k}: </dt><dd className="inline text-ink-3">{v}</dd></div>
                  ))}
                </dl>
              </details>

              <button
                type="submit"
                disabled={prediction.isLoading}
                className="flex w-full md:col-span-2 xl:col-span-1 items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-flame to-ember px-5 py-3.5 text-sm font-bold uppercase tracking-[0.16em] text-space-950 shadow-[0_0_36px_-8px_rgb(251_146_60/0.7)] transition hover:shadow-[0_0_48px_-6px_rgb(251_146_60/0.85)] disabled:opacity-60"
              >
                {prediction.isLoading ? <Loader2 className="size-4 animate-spin" aria-hidden="true" /> : <Zap className="size-4" aria-hidden="true" />}
                Analyze fire risk
              </button>
            </form>
          )}
        </Panel>

        {/* analysis */}
        <Panel
          title="AI analysis"
          provenance="prediction"
          description={submitted ? describeConditions(submitted) : "Model prediction for the conditions on the left."}
          delay={0.12}
        >
          <div aria-live="polite" className="space-y-6">
            {prediction.error ? (
              <ErrorState message={prediction.error.message} onRetry={analyze} />
            ) : !submitted ? (
              <EmptyState title="Ready for analysis" icon={<Radar className="size-5" aria-hidden="true" />}>
                Adjust the conditions, then press <span className="font-semibold text-flame">Analyze fire risk</span>.
              </EmptyState>
            ) : (
              <>
                {stale && (
                  <p className="flex items-center gap-2 rounded-lg border border-plasma/25 bg-plasma/[0.06] px-3 py-2 text-xs text-ink-2">
                    <RefreshCw className="size-3.5 text-plasma" aria-hidden="true" />
                    Conditions changed — showing the previous analysis. Press Analyze to update.
                  </p>
                )}
                <RiskGauge score={result?.fire_risk ?? null} level={result?.risk_level ?? null} alert={alert} dimmed={stale || prediction.isLoading} />
                {result && (
                  <div className={cn("space-y-6 transition-opacity", (stale || prediction.isLoading) && "opacity-45")}>
                    <div className="flex flex-wrap items-center justify-center gap-3">
                      <RiskBadge level={result.risk_level} />
                      {!result.evidence.supported_by_data && (
                        <span className="rounded-full border border-risk-elevated/40 bg-risk-elevated/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.12em] text-risk-elevated">
                          Extrapolation
                        </span>
                      )}
                    </div>
                    <ProbabilityBars sustained={result.sustained_probability} extinction={result.extinction_probability} />
                    <EvidencePanel result={result} />
                  </div>
                )}
              </>
            )}
          </div>
        </Panel>
      </div>

      {result && (
        <div className={cn("grid gap-4 transition-opacity xl:grid-cols-[minmax(0,7fr)_minmax(0,5fr)] xl:gap-6", stale && "opacity-45")}>
          <Panel
            title="Why this prediction?"
            provenance="explanation"
            description="How each input moved the Fire Risk away from the average FLEX test."
            delay={0.05}
          >
            <ContributionWaterfall
              key={JSON.stringify(result.conditions)}
              explanation={result.explanation}
              fireRisk={result.fire_risk}
              alert={alert}
              globalImportance={model.data?.global_importance}
            />
          </Panel>
          <Panel title="AI interpretation" provenance="interpretation" description="The analysis in plain language." delay={0.12}>
            <InterpretationCard key={JSON.stringify(result.conditions)} interpretation={result.interpretation} />
          </Panel>
        </div>
      )}

      {submitted && (
        <Panel
          title="Most similar NASA tests"
          provenance="observed"
          description="Real ISS results closest to these conditions — check the prediction against the evidence."
          delay={0.05}
        >
          {similar.error ? (
            <ErrorState message={similar.error.message} />
          ) : similar.data ? (
            <div className={cn("transition-opacity", stale && "opacity-45")}>
              <NearestTests similar={similar.data} />
            </div>
          ) : (
            <LoadingState rows={3} />
          )}
        </Panel>
      )}

      {result && (
        <div className="flex flex-wrap items-center gap-2 text-xs text-ink-3">
          <ProvenanceBadge kind="prediction" compact /> {result.model}
        </div>
      )}
    </div>
  );
}
