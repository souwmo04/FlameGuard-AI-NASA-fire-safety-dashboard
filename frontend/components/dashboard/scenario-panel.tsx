"use client";

import { ArrowRight, TriangleAlert } from "lucide-react";
import Link from "next/link";

import { ProvenanceBadge } from "@/components/ui/provenance-badge";
import { RiskBadge } from "@/components/ui/risk-badge";
import { LoadingState } from "@/components/ui/states";
import { describeConditions } from "@/lib/conditions";
import { formatPercent } from "@/lib/format";
import type { Conditions, PredictResponse } from "@/lib/types";

interface ScenarioPanelProps {
  conditions: Conditions;
  isReference: boolean;
  result: PredictResponse | undefined;
}

/** The scenario behind the Fire Risk card: conditions, band evidence and the template interpretation. */
export function ScenarioPanel({ conditions, isReference, result }: ScenarioPanelProps) {
  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-2">
        <ProvenanceBadge kind="hypothetical" compact />
        <span className="font-mono text-xs text-ink-2">{describeConditions(conditions)}</span>
      </div>
      {!result ? (
        <LoadingState rows={4} label="Running the model" />
      ) : (
        <>
          <div className="flex flex-wrap items-center gap-3">
            <RiskBadge level={result.risk_level} />
            <span className="text-xs text-ink-3">
              {formatPercent(result.evidence.band.observed_sustained_rate)} of {result.evidence.band.tests} FLEX tests in this
              band kept burning (cross-validated)
            </span>
          </div>
          {!result.evidence.supported_by_data && (
            <p className="flex items-start gap-2 rounded-lg border border-risk-elevated/30 bg-risk-elevated/[0.06] p-3 text-xs text-ink-2">
              <TriangleAlert className="mt-0.5 size-3.5 shrink-0 text-risk-elevated" aria-hidden="true" />
              Extrapolation: these conditions are far from any tested FLEX condition.
            </p>
          )}
          <div className="space-y-2 rounded-xl border border-white/[0.06] bg-white/[0.02] p-4">
            <ProvenanceBadge kind="interpretation" compact />
            <p className="text-sm leading-relaxed text-ink-2">{result.interpretation.text}</p>
          </div>
        </>
      )}
      <Link href="/risk" className="inline-flex items-center gap-1.5 text-sm font-medium text-flame hover:underline">
        {isReference ? "Analyze your own scenario" : "Refine this analysis"} <ArrowRight className="size-4" aria-hidden="true" />
      </Link>
    </div>
  );
}
