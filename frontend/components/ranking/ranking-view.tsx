"use client";

import { Brain, FlaskConical, Timer } from "lucide-react";
import { useState } from "react";

import { Panel } from "@/components/dashboard/panel";
import { Segmented } from "@/components/risk/segmented";
import { PageHeader } from "@/components/ui/page-header";
import { ProvenanceBadge } from "@/components/ui/provenance-badge";
import { ErrorState, LoadingState } from "@/components/ui/states";
import { Tabs } from "@/components/ui/tabs";
import { useApi } from "@/hooks/use-api";
import { endpoints } from "@/lib/api";
import { formatPercent } from "@/lib/format";
import type { ConditionRankingResponse, RankingResponse } from "@/lib/types";

import { ConditionForest } from "./condition-forest";
import { TestRankingList } from "./test-ranking-list";

type View = "conditions" | "model" | "burn";
type FuelChoice = "all" | "Methanol" | "Heptane";

const FUELS = [{ value: "all" as const, label: "Both fuels" }, { value: "Methanol" as const, label: "Methanol" }, { value: "Heptane" as const, label: "n-Heptane" }];
const LIMIT = 20;

function ConditionsView({ fuel }: { fuel: FuelChoice }) {
  const [order, setOrder] = useState<"desc" | "asc">("desc");
  const res = useApi<ConditionRankingResponse>(`${endpoints.conditionRanking}?order=desc&limit=100`);
  if (res.error) return <ErrorState message={res.error.message} onRetry={() => res.mutate()} />;
  if (!res.data) return <LoadingState rows={8} />;
  const items = res.data.items.filter((c) => fuel === "all" || c.fuel === fuel);
  return (
    <div className="space-y-5">
      <div className="max-w-md">
        <Segmented<"desc" | "asc"> label="Order" value={order} onChange={setOrder}
          options={[{ value: "desc", label: "Kept burning most" }, { value: "asc", label: "Went out most" }]} />
      </div>
      <ConditionForest key={`${fuel}-${order}`} items={items} order={order} />
      <p className="text-xs leading-relaxed text-ink-3">{res.data.method} Intervals are wide for small groups — two conditions whose intervals overlap are not shown to differ.</p>
    </div>
  );
}

function ModelView({ fuel }: { fuel: FuelChoice }) {
  const [by, setBy] = useState<"risk" | "lowest_risk">("risk");
  const res = useApi<RankingResponse>(`${endpoints.ranking}?by=${by}&limit=${LIMIT}${fuel === "all" ? "" : `&fuel=${fuel}`}`, { keepPreviousData: true });
  if (res.error) return <ErrorState message={res.error.message} onRetry={() => res.mutate()} />;
  if (!res.data) return <LoadingState rows={8} />;
  const kept = res.data.items.filter((i) => i.experiment.sustained).length;
  const n = res.data.items.length;
  return (
    <div className="space-y-5">
      <div className="max-w-md">
        <Segmented<"risk" | "lowest_risk"> label="Order" value={by} onChange={setBy}
          options={[{ value: "risk", label: "Highest Fire Risk" }, { value: "lowest_risk", label: "Lowest Fire Risk" }]} />
      </div>
      <div className="flex flex-wrap items-center gap-3 rounded-xl border border-white/[0.06] bg-white/[0.02] p-3.5">
        <ProvenanceBadge kind="evaluation" compact />
        <p className="text-sm text-ink-2">
          Reality check: of the {n} tests the model rated {by === "risk" ? "highest" : "lowest"}, <span className="font-semibold text-ink">{kept}</span> actually kept burning
          ({formatPercent(kept / Math.max(1, n))}).
        </p>
      </div>
      <TestRankingList data={res.data} />
      <p className="text-xs leading-relaxed text-ink-3">{res.data.method} Several tests share identical conditions, so they share a score.</p>
    </div>
  );
}

function BurnView({ fuel }: { fuel: FuelChoice }) {
  const res = useApi<RankingResponse>(`${endpoints.ranking}?by=burn_time&limit=${LIMIT}${fuel === "all" ? "" : `&fuel=${fuel}`}`, { keepPreviousData: true });
  if (res.error) return <ErrorState message={res.error.message} onRetry={() => res.mutate()} />;
  if (!res.data) return <LoadingState rows={8} />;
  return (
    <div className="space-y-5">
      <TestRankingList data={res.data} />
      <p className="text-xs leading-relaxed text-ink-3">
        {res.data.method} Burn time depends strongly on the initial droplet size, so long burns are not directly comparable across sizes.
      </p>
    </div>
  );
}

export function RankingView() {
  const [view, setView] = useState<View>("conditions");
  const [fuel, setFuel] = useState<FuelChoice>("all");
  const meta = {
    conditions: { title: "Tested atmospheres", provenance: "observed" as const, description: "Share of ISS tests that kept burning in each tested atmosphere (at least 3 tests)." },
    model: { title: "The model's ranking", provenance: "prediction" as const, description: "Tests ranked by out-of-fold Fire Risk, shown next to what actually happened." },
    burn: { title: "Longest burns", provenance: "observed" as const, description: "Measured burn times on the ISS." },
  }[view];

  return (
    <div className="space-y-6 lg:space-y-8">
      <PageHeader
        eyebrow="Ranking"
        title="Risk Ranking"
        subtitle="Which conditions kept flames alive most often, which tests the model rates highest and lowest, and how both compare with what NASA observed."
      />
      <Panel title={meta.title} provenance={meta.provenance} description={meta.description}
        actions={<div className="w-full min-w-0 sm:w-72"><Segmented<FuelChoice> label="Fuel" value={fuel} onChange={setFuel} options={FUELS} /></div>}>
        <Tabs<View> label="Ranking type" value={view} onChange={setView} items={[
          { value: "conditions", label: "Tested atmospheres", icon: FlaskConical },
          { value: "model", label: "Model ranking", icon: Brain },
          { value: "burn", label: "Longest burns", icon: Timer },
        ]}>
          {view === "conditions" && <ConditionsView fuel={fuel} />}
          {view === "model" && <ModelView fuel={fuel} />}
          {view === "burn" && <BurnView fuel={fuel} />}
        </Tabs>
      </Panel>
    </div>
  );
}
