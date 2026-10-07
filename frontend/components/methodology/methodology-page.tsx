"use client";

import { BookMarked, Database, Filter, FlaskConical, GitBranch, Layers, Scale, ShieldCheck, Sigma, Target, TriangleAlert, Wand2 } from "lucide-react";
import { motion } from "motion/react";
import Link from "next/link";
import type { ReactNode } from "react";

import { Panel } from "@/components/dashboard/panel";
import { GlassCard } from "@/components/ui/glass-card";
import { PageHeader } from "@/components/ui/page-header";
import { ProvenanceBadge } from "@/components/ui/provenance-badge";
import { RiskBadge } from "@/components/ui/risk-badge";
import { ErrorState, LoadingState } from "@/components/ui/states";
import { useApi } from "@/hooks/use-api";
import { endpoints } from "@/lib/api";
import { RISK_COLORS } from "@/lib/chart-theme";
import { formatPercent } from "@/lib/format";
import type { ModelInfoResponse, StatsResponse } from "@/lib/types";

import { CalibrationChart } from "./calibration-chart";

const REPO = "https://github.com/souwmo04/FlameGuard-AI-NASA-fire-safety-dashboard/blob/main";

const FEATURE_LABEL: Record<string, string> = {
  is_heptane: "Fuel is n-heptane",
  x_o2: "Oxygen fraction",
  x_co2: "CO₂ fraction",
  x_he: "Helium fraction",
  d0_mm: "Droplet diameter",
  heptane_x_d0: "Heptane × droplet diameter",
};

function Step({ icon: Icon, title, children, i }: { icon: typeof Database; title: string; children: ReactNode; i: number }) {
  return (
    <motion.li initial={{ opacity: 0, y: 10 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: i * 0.05 }}
      className="relative flex gap-3 rounded-xl border border-white/[0.06] bg-white/[0.02] p-4">
      <span className="inline-flex size-8 shrink-0 items-center justify-center rounded-lg bg-flame/10 text-flame"><Icon className="size-4" aria-hidden="true" /></span>
      <div className="min-w-0 space-y-1">
        <p className="flex items-center gap-2 text-sm font-semibold text-ink"><span className="font-mono text-xs text-ink-3">{String(i + 1).padStart(2, "0")}</span>{title}</p>
        <p className="text-xs leading-relaxed text-ink-2">{children}</p>
      </div>
    </motion.li>
  );
}

const doc = (path: string, label: string) => (
  <a href={`${REPO}/${path}`} target="_blank" rel="noreferrer" className="text-plasma hover:underline">{label}</a>
);

export function MethodologyPage() {
  const model = useApi<ModelInfoResponse>(endpoints.model);
  const stats = useApi<StatsResponse>(endpoints.stats);
  const m = model.data;
  const e = stats.data?.experiments;

  const header = (
    <PageHeader
      eyebrow="Methodology"
      title="How FlameGuard Works"
      subtitle="From NASA's raw ISS measurements to a calibrated Fire Risk score: every step, every number and every known weakness. All metrics are cross-validated on tests the model never saw."
    />
  );
  if (model.error) return <div className="space-y-6">{header}<ErrorState message={model.error.message} onRetry={() => model.mutate()} /></div>;
  if (!m) return <div className="space-y-6">{header}<LoadingState rows={12} label="Loading model card" /></div>;

  const maxCoef = Math.max(...Object.values(m.standardised_coefficients).map(Math.abs));

  return (
    <div className="space-y-8 lg:space-y-10">
      {header}

      <Panel title="The pipeline" provenance="observed" description="Each step is a script in the repository; outputs are committed so every number can be traced.">
        <ol className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          <Step i={0} icon={Database} title="NASA data">FLEX droplet tests from NASA Physical Sciences Informatics (PSI-69, CC0), {e?.total ?? 274} tests on the ISS, 2009–2011. Raw files are checksummed and never edited. {doc("docs/data_card.md", "Data card")}</Step>
          <Step i={1} icon={Filter} title="Cleaning and scope">Encoding, units and identifiers are fixed with quality flags. The model uses the {m.training_tests} tests at 0.7–1 atm with a known droplet size; every other test keeps a recorded reason.</Step>
          <Step i={2} icon={Target} title="Target">Sustained burning = the droplet burned to completion or disrupted (1) versus self-extinguished (0): {m.training_sustained} of {m.training_tests}. Fixed before any model was trained. {doc("docs/target_features_validation.md", "Design")}</Step>
          <Step i={3} icon={Layers} title="Validation">{m.validation}. Tests sharing a chamber atmosphere never span train and test, so the score measures generalisation to new atmospheres.</Step>
          <Step i={4} icon={Scale} title="Model selection">Logistic regression, random forest and XGBoost, each with and without tuning, were compared under the same folds. A rule fixed in advance selected: {m.name}.</Step>
          <Step i={5} icon={ShieldCheck} title="Calibration and bands">Fire Risk = 100 × predicted probability. LOW / ELEVATED / HIGH bands and the alert threshold come from out-of-fold predictions, with each band&apos;s observed track record.</Step>
          <Step i={6} icon={Wand2} title="Explanations">Exact Shapley values on the raw inputs, fuel first, atmosphere grouped (O₂ + CO₂ + He). They describe the model, not physical causes.</Step>
          <Step i={7} icon={Sigma} title="Observed-data analyses">Suppressant thresholds (O₂₅₀), condition rankings and similar-test search use observed tests only, with intervals and no ML model.</Step>
          <Step i={8} icon={BookMarked} title="Grounded assistant">Ask FlameGuard answers only from the NASA report and these documents, citing every claim.</Step>
        </ol>
      </Panel>

      <div className="grid gap-4 xl:grid-cols-2 xl:gap-6">
        <Panel title="Performance on unseen tests" provenance="evaluation" description="Mean ± sd over 25 grouped folds, and pooled out-of-fold estimate with 95% bootstrap interval.">
          <table className="w-full text-sm">
            <caption className="sr-only">Cross-validated metrics</caption>
            <thead>
              <tr className="text-left">
                <th scope="col" className="label-caps pb-2 text-[0.625rem]">Metric</th>
                <th scope="col" className="label-caps pb-2 text-right text-[0.625rem]">Mean ± sd</th>
                <th scope="col" className="label-caps hidden pb-2 text-right text-[0.625rem] sm:table-cell">Pooled (95% CI)</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/[0.05]">
              {m.metrics.map((x) => (
                <tr key={x.name}>
                  <th scope="row" className="py-2 pr-3 text-left font-normal text-ink-2">{x.name}</th>
                  <td className="whitespace-nowrap py-2 text-right font-mono tabular-nums text-ink">{x.nested_mean.toFixed(3)} <span className="text-ink-3">± {x.nested_sd.toFixed(3)}</span></td>
                  <td className="hidden whitespace-nowrap py-2 pl-3 text-right font-mono text-xs tabular-nums text-ink-3 sm:table-cell">
                    {x.pooled_estimate !== null ? x.pooled_estimate.toFixed(3) : "—"}
                    {x.pooled_ci_low !== null && x.pooled_ci_high !== null && ` (${x.pooled_ci_low.toFixed(3)}–${x.pooled_ci_high.toFixed(3)})`}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Panel>
        <Panel title="Calibration" provenance="evaluation" description="Does a predicted 30% really mean about 30% of such droplets kept burning?">
          <CalibrationChart bins={m.calibration} />
        </Panel>
      </div>

      <div className="grid gap-4 xl:grid-cols-2 xl:gap-6">
        <Panel title="Risk bands and their track record" provenance="evaluation" description="Share of tests in each band that actually kept burning (out-of-fold).">
          <ul className="space-y-4">
            {m.bands.map((b) => (
              <li key={b.level} className="space-y-2">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <RiskBadge level={b.level} />
                  <span className="font-mono text-xs text-ink-3">score {b.score_from}–{b.score_to} · {b.tests} tests</span>
                </div>
                <div className="relative h-2 overflow-hidden rounded-full bg-white/[0.06]" aria-hidden="true">
                  <span className="absolute inset-y-0 rounded-full opacity-30" style={{ left: `${b.ci_low * 100}%`, width: `${(b.ci_high - b.ci_low) * 100}%`, background: RISK_COLORS[b.level] }} />
                  <motion.span className="absolute inset-y-0 left-0 rounded-full" style={{ background: RISK_COLORS[b.level] }}
                    initial={{ width: 0 }} whileInView={{ width: `${b.observed_sustained_rate * 100}%` }} viewport={{ once: true }} transition={{ duration: 0.8 }} />
                </div>
                <p className="text-xs text-ink-2">
                  <span className="font-semibold text-ink">{formatPercent(b.observed_sustained_rate)}</span> kept burning ({b.sustained}/{b.tests}; 95% CI {formatPercent(b.ci_low)}–{formatPercent(b.ci_high)})
                </p>
              </li>
            ))}
          </ul>
        </Panel>
        <Panel title="What the model learned" provenance="explanation" description="Standardised logistic coefficients: direction and relative weight of each input.">
          <ul className="space-y-2.5">
            {Object.entries(m.standardised_coefficients).sort((a, b) => Math.abs(b[1]) - Math.abs(a[1])).map(([k, v]) => (
              <li key={k} className="grid grid-cols-[10rem_minmax(0,1fr)_3.5rem] items-center gap-3 text-sm">
                <span className="truncate text-ink-2">{FEATURE_LABEL[k] ?? k}</span>
                <span className="relative h-2 rounded-full bg-white/[0.05]" aria-hidden="true">
                  <span className="absolute inset-y-0 left-1/2 w-px bg-white/20" />
                  <motion.span className={v >= 0 ? "absolute inset-y-0 left-1/2 rounded-r-full bg-risk-high" : "absolute inset-y-0 right-1/2 rounded-l-full bg-plasma"}
                    initial={{ width: 0 }} whileInView={{ width: `${(Math.abs(v) / maxCoef) * 50}%` }} viewport={{ once: true }} transition={{ duration: 0.7 }} />
                </span>
                <span className="text-right font-mono text-xs tabular-nums text-ink">{v > 0 ? "+" : "−"}{Math.abs(v).toFixed(2)}</span>
              </li>
            ))}
          </ul>
          <p className="mt-3 text-xs text-ink-3">Red raises, cyan lowers the predicted chance of sustained burning. The heptane × droplet term means droplet size pushes the two fuels in opposite directions. These are associations in NASA&apos;s test design, not causal effects.</p>
        </Panel>
      </div>

      <Panel title="Where it does well and where it struggles" provenance="evaluation" description="Out-of-fold results by subgroup at the alert threshold.">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[34rem] text-sm">
            <caption className="sr-only">Subgroup performance</caption>
            <thead>
              <tr className="text-left">
                {["Subgroup", "Tests", "Kept burning", "ROC-AUC", "Recall", "Missed fires", "False alarms"].map((h) => (
                  <th key={h} scope="col" className="label-caps pb-2 text-[0.625rem]">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-white/[0.05] font-mono text-xs tabular-nums">
              {m.subgroups.map((g) => (
                <tr key={g.subgroup}>
                  <th scope="row" className="py-2 pr-3 text-left font-sans text-sm font-normal text-ink-2">{g.subgroup.replace("fuel=", "Fuel: ").replace("diluent=", "Diluent: ").replace("pressure=", "Pressure: ")}</th>
                  <td className="py-2 text-ink">{g.tests}</td>
                  <td className="py-2 text-ink">{g.sustained}</td>
                  <td className="py-2 text-ink">{g.roc_auc !== null && g.roc_auc !== undefined ? g.roc_auc.toFixed(3) : "—"}</td>
                  <td className="py-2 text-ink">{g.recall !== null && g.recall !== undefined ? formatPercent(g.recall) : "—"}</td>
                  <td className="py-2 text-risk-high">{g.missed_fires}</td>
                  <td className="py-2 text-ink-3">{g.false_alarms}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {m.consistently_missed_test_ids.length > 0 && (
          <p className="mt-3 flex flex-wrap items-center gap-1.5 text-xs text-ink-3">
            Fires missed in most cross-validation repeats:
            {m.consistently_missed_test_ids.map((id) => (
              <Link key={id} href={`/experiments?test=${id}`} className="rounded-md border border-white/10 px-1.5 py-0.5 font-mono text-ink-2 hover:border-risk-high/40 hover:text-risk-high">
                {String(id).padStart(3, "0")}
              </Link>
            ))}
          </p>
        )}
      </Panel>

      <div className="grid gap-4 xl:grid-cols-2 xl:gap-6">
        <Panel title="Design decisions" description="Changes to the pre-registered design, with their evidence.">
          <ul className="space-y-3">
            <li>
              <GlassCard className="space-y-1.5 p-4">
                <p className="flex items-center gap-2 text-sm font-semibold text-ink"><GitBranch className="size-4 text-flame" aria-hidden="true" />D-001 · Pressure removed as an input</p>
                <p className="text-xs leading-relaxed text-ink-2">FLEX ran at only ~0.7 and ~1 atm. With pressure as an input, predictions collapsed when trained on one level and tested on the other; without it, skill was unchanged. Pressure still limits the model&apos;s scope to 0.7–1 atm.</p>
              </GlassCard>
            </li>
            <li>
              <GlassCard className="space-y-1.5 border-risk-elevated/25 p-4">
                <p className="flex items-center gap-2 text-sm font-semibold text-ink"><FlaskConical className="size-4 text-risk-elevated" aria-hidden="true" />D-002 · Fuel-needle contamination</p>
                <p className="text-xs leading-relaxed text-ink-2">NASA links methanol disruptions probably to a needle coating. Refitting without them barely changes heptane but lowers methanol scores sharply (air, 3 mm: 29 → 8). The model is unchanged pending the project owner&apos;s decision; every methanol prediction shows this contamination check.</p>
              </GlassCard>
            </li>
          </ul>
          <p className="mt-3 text-xs text-ink-3">Full evidence: {doc("docs/decisions.md", "decision log")} · {doc("docs/model_card.md", "model card")}.</p>
        </Panel>
        <Panel title="Known limitations" provenance="evaluation">
          <ul className="space-y-2.5">
            {m.limitations.map((l) => (
              <li key={l} className="flex gap-2.5 text-sm text-ink-2">
                <TriangleAlert className="mt-0.5 size-4 shrink-0 text-risk-elevated" aria-hidden="true" />{l}
              </li>
            ))}
          </ul>
        </Panel>
      </div>

      <Panel title="Reproduce everything" description="The full pipeline runs from the raw NASA files on a laptop.">
        <pre className="overflow-x-auto rounded-xl border border-white/[0.06] bg-space-950/80 p-4 font-mono text-xs leading-relaxed text-ink-2">{`python scripts/download_flex.py          # raw NASA data + FLEX report
python scripts/build_master.py           # cleaning -> data/processed/
python scripts/train_baselines.py        # cross-validated baselines
python scripts/phase8_experiments.py     # tuning, ablation, sensitivity, stress tests
python scripts/finalize_model.py         # calibration, risk bands, final model
python scripts/explain_model.py          # Shapley explanations
python scripts/suppressant_analysis.py   # O2-50 per test series
python scripts/contamination_sensitivity.py  # decision D-002
python scripts/build_knowledge.py        # Ask FlameGuard corpus
python -m pytest                         # library + API tests`}</pre>
        <p className="mt-3 flex flex-wrap items-center gap-2 text-xs text-ink-3">
          <ProvenanceBadge kind="evaluation" compact /> Every metric on this page is computed by these scripts; nothing is typed in by hand.
        </p>
      </Panel>
    </div>
  );
}
