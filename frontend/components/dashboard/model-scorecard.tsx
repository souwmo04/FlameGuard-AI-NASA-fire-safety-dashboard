import type { ModelInfoResponse } from "@/lib/types";

const SHOW = ["ROC-AUC", "PR-AUC", "Brier score", "Recall at alert threshold", "Precision at alert threshold", "Missed-fire rate"];

/** Cross-validated metrics: nested mean ± sd, with the pooled 95% bootstrap interval when available. */
export function ModelScorecard({ model }: { model: ModelInfoResponse }) {
  const rows = model.metrics.filter((m) => SHOW.includes(m.name));
  return (
    <div className="space-y-3">
      <table className="w-full text-sm">
        <caption className="sr-only">Model performance on held-out FLEX tests</caption>
        <thead>
          <tr className="text-left">
            <th scope="col" className="label-caps pb-2 font-semibold">Metric</th>
            <th scope="col" className="label-caps pb-2 text-right font-semibold">Mean ± sd</th>
            <th scope="col" className="label-caps hidden pb-2 text-right font-semibold xl:table-cell">95% CI</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-white/[0.05]">
          {rows.map((m) => (
            <tr key={m.name}>
              <th scope="row" className="py-2 pr-3 text-left font-normal text-ink-2">{m.name}</th>
              <td className="py-2 text-right font-mono tabular-nums text-ink">
                {m.nested_mean.toFixed(3)} <span className="text-ink-3">± {m.nested_sd.toFixed(3)}</span>
              </td>
              <td className="hidden py-2 text-right font-mono text-xs tabular-nums text-ink-3 xl:table-cell">
                {m.pooled_ci_low !== null && m.pooled_ci_high !== null ? `${m.pooled_ci_low.toFixed(3)}–${m.pooled_ci_high.toFixed(3)}` : "—"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className="text-xs text-ink-3">
        {model.training_tests} tests ({model.training_sustained} sustained). {model.validation}.
      </p>
    </div>
  );
}
