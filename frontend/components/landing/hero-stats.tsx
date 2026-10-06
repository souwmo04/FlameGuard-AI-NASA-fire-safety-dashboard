"use client";

import { BrainCircuit, Droplets, FlaskConical, ShieldCheck } from "lucide-react";

import { MetricCard } from "@/components/ui/metric-card";
import { ErrorState } from "@/components/ui/states";
import { useApi } from "@/hooks/use-api";
import { endpoints } from "@/lib/api";
import { formatDecimal, formatInt } from "@/lib/format";
import type { StatsResponse } from "@/lib/types";

/** Headline numbers, all read live from GET /api/stats (nothing hard-coded). */
export function HeroStats() {
  const { data, error, mutate } = useApi<StatsResponse>(endpoints.stats);

  if (error) {
    return <ErrorState message={`Live statistics are unavailable. ${error.message}`} onRetry={() => mutate()} />;
  }

  const e = data?.experiments;
  return (
    <div className="grid grid-cols-2 gap-3 sm:gap-4 lg:grid-cols-4">
      <MetricCard
        label="ISS combustion tests"
        value={e?.total ?? null}
        format={formatInt}
        icon={FlaskConical}
        accent="plasma"
        provenance="observed"
        hint={data ? <span>NASA FLEX · {data.date_start.slice(0, 4)}–{data.date_end.slice(0, 4)}</span> : null}
        delay={0.05}
      />
      <MetricCard
        label="Flames that self-extinguished"
        value={e?.extinction ?? null}
        format={formatInt}
        icon={ShieldCheck}
        accent="plasma"
        provenance="observed"
        hint={e ? <span>{e.sustained} kept burning</span> : null}
        delay={0.12}
      />
      <MetricCard
        label="Fuels tested"
        value={data ? data.fuels.length : null}
        format={formatInt}
        icon={Droplets}
        accent="neutral"
        provenance="observed"
        hint={data ? <span>{data.fuels.map((f) => (f === "Heptane" ? "n-heptane" : f.toLowerCase())).join(" · ")}</span> : null}
        delay={0.19}
      />
      <MetricCard
        label="Model ROC-AUC"
        value={data ? data.model.roc_auc : null}
        format={(n) => formatDecimal(n, 3)}
        icon={BrainCircuit}
        accent="flame"
        provenance="evaluation"
        hint={data ? <span>± {formatDecimal(data.model.roc_auc_sd, 3)} · 25 held-out folds</span> : null}
        delay={0.26}
      />
    </div>
  );
}
