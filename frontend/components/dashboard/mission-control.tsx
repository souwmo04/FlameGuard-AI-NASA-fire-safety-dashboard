"use client";

import { Activity, BrainCircuit, Database, Flame, FlaskConical, Satellite, ShieldCheck } from "lucide-react";
import { motion } from "motion/react";

import { GlassCard } from "@/components/ui/glass-card";
import { MetricCard } from "@/components/ui/metric-card";
import { PageHeader } from "@/components/ui/page-header";
import { ErrorState, LoadingState } from "@/components/ui/states";
import { ButtonLink } from "@/components/ui/button-link";
import { useApi } from "@/hooks/use-api";
import { usePredict } from "@/hooks/use-predict";
import { endpoints } from "@/lib/api";
import { cn } from "@/lib/cn";
import { formatInt, formatPercent, formatRisk } from "@/lib/format";
import { REFERENCE_SCENARIO, useLastAnalysis } from "@/lib/last-analysis";
import type { ExperimentList, HealthResponse, ModelInfoResponse, Source, StatsResponse } from "@/lib/types";

import { BandEvidence } from "./band-evidence";
import { ConditionMap } from "./condition-map";
import { ImportanceBars } from "./importance-bars";
import { ModelScorecard } from "./model-scorecard";
import { OutcomeDonut } from "./outcome-donut";
import { Panel } from "./panel";
import { ScenarioPanel } from "./scenario-panel";
import { SourcesList } from "./sources-list";

export function MissionControl() {
  const stats = useApi<StatsResponse>(endpoints.stats);
  const model = useApi<ModelInfoResponse>(endpoints.model);
  const sources = useApi<Source[]>(endpoints.sources);
  const health = useApi<HealthResponse>(endpoints.health, { refreshInterval: 30_000 });
  const experiments = useApi<ExperimentList>(`${endpoints.experiments}?limit=300`);

  const last = useLastAnalysis();
  const scenario = last ?? REFERENCE_SCENARIO;
  const prediction = usePredict(scenario);
  const scenarioLabel = last ? "your last analysis" : "reference scenario";

  const offline = stats.error ?? model.error;

  return (
    <div className="space-y-6 lg:space-y-8">
      <PageHeader
        eyebrow="Mission Control"
        title="Mission Control"
        subtitle="Microgravity combustion intelligence — NASA FLEX evidence, model status and the current scenario at a glance."
        actions={<ButtonLink href="/risk" className="px-4 py-2.5">Run analysis</ButtonLink>}
      />

      {offline && (
        <ErrorState
          message={`Mission Control cannot reach the API. ${offline.message}`}
          onRetry={() => { stats.mutate(); model.mutate(); sources.mutate(); experiments.mutate(); prediction.mutate(); }}
        />
      )}

      {/* status cards */}
      <div className="grid grid-cols-2 gap-3 sm:gap-4 lg:grid-cols-5">
        <MetricCard
          label="Fire risk"
          value={prediction.data?.fire_risk ?? null}
          format={formatRisk}
          icon={Flame}
          accent="flame"
          provenance="prediction"
          hint={<span>{scenarioLabel}</span>}
          delay={0}
        />
        <MetricCard
          label="Extinction probability"
          value={prediction.data ? prediction.data.extinction_probability * 100 : null}
          format={(n) => `${Math.round(n)}%`}
          icon={ShieldCheck}
          accent="plasma"
          provenance="prediction"
          hint={<span>{scenarioLabel}</span>}
          delay={0.06}
        />
        <MetricCard
          label="FLEX experiments"
          value={stats.data?.experiments.total ?? null}
          format={formatInt}
          icon={FlaskConical}
          provenance="observed"
          hint={stats.data ? <span>{stats.data.experiments.in_model_scope} used for training</span> : null}
          delay={0.12}
        />
        <MetricCard
          label="NASA sources"
          value={sources.data?.length ?? null}
          format={formatInt}
          icon={Satellite}
          hint={sources.data ? <span>dataset + technical report</span> : null}
          delay={0.18}
        />
        <ModelStatusCard health={health.data} error={!!health.error} model={model.data} className="col-span-2 lg:col-span-1" />
      </div>

      <div className="grid gap-4 lg:grid-cols-5 lg:gap-6">
        <Panel
          title={last ? "Your last analysis" : "Reference scenario"}
          description={last ? "From the Fire Risk page." : "Methanol in air-like oxygen — a starting point until you run your own analysis."}
          provenance="prediction"
          className="lg:col-span-3"
          delay={0.1}
        >
          <ScenarioPanel conditions={scenario} isReference={!last} result={prediction.data} />
        </Panel>
        <Panel title="What NASA observed" description="Outcome of every FLEX droplet test." provenance="observed" className="lg:col-span-2" delay={0.16}>
          {stats.data ? <OutcomeDonut stats={stats.data} /> : <LoadingState rows={5} />}
        </Panel>
      </div>

      <div className="grid gap-4 lg:grid-cols-5 lg:gap-6">
        <Panel
          title="Condition map"
          description="Where each ISS test sat in oxygen and droplet size, and how it ended."
          provenance="observed"
          className="lg:col-span-3"
          delay={0.2}
        >
          {experiments.data ? <ConditionMap experiments={experiments.data.items} /> : <LoadingState rows={6} />}
        </Panel>
        <Panel
          title="Do the risk bands mean anything?"
          description="Share of tests that kept burning, per band."
          provenance="evaluation"
          className="lg:col-span-2"
          delay={0.24}
        >
          {model.data ? <BandEvidence model={model.data} /> : <LoadingState rows={5} />}
        </Panel>
      </div>

      <div className="grid gap-4 lg:grid-cols-3 lg:gap-6">
        <Panel title="What drives the model" provenance="explanation" delay={0.28}>
          {model.data ? <ImportanceBars model={model.data} /> : <LoadingState rows={4} />}
        </Panel>
        <Panel title="Model scorecard" description="On tests the model never saw." provenance="evaluation" delay={0.32}>
          {model.data ? <ModelScorecard model={model.data} /> : <LoadingState rows={6} />}
        </Panel>
        <Panel title="NASA sources" provenance="observed" delay={0.36}>
          {sources.data ? <SourcesList sources={sources.data} /> : <LoadingState rows={4} />}
        </Panel>
      </div>

      {model.data && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.4 }}>
          <GlassCard className="p-5 sm:p-6">
            <h2 className="label-caps mb-3">Known limitations</h2>
            <ul className="grid gap-2 text-sm text-ink-2 md:grid-cols-2">
              {model.data.limitations.map((l) => (
                <li key={l} className="flex gap-2"><span aria-hidden="true" className="text-flame">•</span>{l}</li>
              ))}
            </ul>
          </GlassCard>
        </motion.div>
      )}
    </div>
  );
}

function ModelStatusCard({ health, error, model, className }: {
  health: HealthResponse | undefined;
  error: boolean;
  model: ModelInfoResponse | undefined;
  className?: string;
}) {
  const online = !!health && !error;
  const auc = model?.metrics.find((m) => m.name === "ROC-AUC");
  return (
    <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.45, delay: 0.24 }} className={className}>
      <GlassCard className="flex h-full flex-col gap-3 p-5">
        <div className="flex items-center justify-between">
          <span className="label-caps">Model status</span>
          <BrainCircuit className="size-4 text-prov-prediction" aria-hidden="true" />
        </div>
        <div className={cn("flex items-center gap-2 font-display text-2xl font-semibold", online ? "text-risk-low" : "text-risk-high")}>
          {online ? <Activity className="size-5" aria-hidden="true" /> : <Database className="size-5" aria-hidden="true" />}
          {online ? "Online" : error ? "Offline" : "…"}
        </div>
        <p className="mt-auto text-xs text-ink-2">
          {online && health ? `Logistic regression · ${health.training_tests} training tests` : "Start the FastAPI backend"}
          {auc && <span className="block text-ink-3">ROC-AUC {auc.nested_mean.toFixed(3)} · recall {formatPercent(model?.metrics.find((m) => m.name === "Recall at alert threshold")?.nested_mean ?? 0)}</span>}
        </p>
      </GlassCard>
    </motion.div>
  );
}
