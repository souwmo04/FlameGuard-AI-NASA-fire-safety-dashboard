import { CircleCheck, CircleX, TriangleAlert } from "lucide-react";

import { ProvenanceBadge } from "@/components/ui/provenance-badge";
import { formatPercent } from "@/lib/format";
import type { PredictResponse } from "@/lib/types";

/** How much the data supports this prediction: domain checks, band track record, warnings. */
export function EvidencePanel({ result }: { result: PredictResponse }) {
  const e = result.evidence;
  const checks = [
    {
      ok: e.in_tested_range,
      title: e.in_tested_range ? "Every input inside the tested range" : "An input is outside the tested range",
      detail: "Ranges tested for this fuel in NASA FLEX.",
    },
    {
      ok: e.supported_by_data,
      title: e.supported_by_data ? "Close to tested NASA conditions" : "Far from any tested condition — extrapolation",
      detail: `Distance to nearest tested atmosphere ${e.nearest_tested_distance.toFixed(2)} (typical spacing ${e.support_radius.toFixed(2)}).`,
    },
  ];
  return (
    <div className="space-y-4">
      <ul className="space-y-3">
        {checks.map((c) => (
          <li key={c.title} className="flex items-start gap-3">
            {c.ok ? (
              <CircleCheck className="mt-0.5 size-4 shrink-0 text-risk-low" aria-label="Pass" />
            ) : (
              <CircleX className="mt-0.5 size-4 shrink-0 text-risk-high" aria-label="Fail" />
            )}
            <div>
              <p className="text-sm text-ink">{c.title}</p>
              <p className="text-xs text-ink-3">{c.detail}</p>
            </div>
          </li>
        ))}
      </ul>

      {e.warnings.length > 0 && (
        <div role="alert" className="space-y-1.5 rounded-xl border border-risk-elevated/30 bg-risk-elevated/[0.06] p-3.5">
          {e.warnings.map((w) => (
            <p key={w} className="flex items-start gap-2 text-xs text-ink-2">
              <TriangleAlert className="mt-0.5 size-3.5 shrink-0 text-risk-elevated" aria-hidden="true" />{w}
            </p>
          ))}
        </div>
      )}

      <div className="space-y-2 rounded-xl border border-white/[0.06] bg-white/[0.02] p-3.5">
        <ProvenanceBadge kind="evaluation" compact />
        <p className="text-sm text-ink-2">
          In cross-validation, <span className="font-semibold text-ink">{formatPercent(e.band.observed_sustained_rate)}</span> of the{" "}
          {e.band.tests} FLEX tests the model placed in the <span className="font-semibold text-ink">{e.band.level}</span> band
          actually kept burning <span className="text-ink-3">(95% CI {formatPercent(e.band.ci_low)}–{formatPercent(e.band.ci_high)})</span>.
        </p>
      </div>
      <p className="text-xs leading-relaxed text-ink-3">{result.scope}</p>
    </div>
  );
}
