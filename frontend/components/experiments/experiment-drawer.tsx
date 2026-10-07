"use client";

import { ArrowUpRight, ExternalLink, FlaskConical, Info, SlidersHorizontal, X } from "lucide-react";
import Link from "next/link";
import { useEffect, useRef, type ReactNode } from "react";

import { OutcomeShape } from "@/components/charts/outcome-shape";
import { ProvenanceBadge } from "@/components/ui/provenance-badge";
import { RiskBadge } from "@/components/ui/risk-badge";
import { LoadingState } from "@/components/ui/states";
import { useApi } from "@/hooks/use-api";
import { endpoints } from "@/lib/api";
import { OUTCOME_COLORS, OUTCOME_LABEL } from "@/lib/chart-theme";
import { formatRisk } from "@/lib/format";
import { conditionsToQuery, experimentConditions } from "@/lib/scenario-url";
import type { ExperimentDetail, ExperimentSummary } from "@/lib/types";

import { testLabel } from "./experiment-table";

function Section({ title, kind, children }: { title: string; kind?: "observed" | "prediction"; children: ReactNode }) {
  return (
    <section className="space-y-3 border-t border-white/[0.06] pt-5">
      <div className="flex items-center justify-between gap-2">
        <h3 className="font-display text-sm font-semibold text-ink">{title}</h3>
        {kind && <ProvenanceBadge kind={kind} compact />}
      </div>
      {children}
    </section>
  );
}

function Facts({ rows }: { rows: [string, ReactNode][] }) {
  return (
    <dl className="grid grid-cols-2 gap-x-4 gap-y-3 sm:grid-cols-3">
      {rows.map(([k, v]) => (
        <div key={k} className="min-w-0">
          <dt className="label-caps text-[0.625rem]">{k}</dt>
          <dd className="mt-0.5 font-mono text-sm tabular-nums text-ink">{v}</dd>
        </div>
      ))}
    </dl>
  );
}

/** How the out-of-fold prediction compares with what was observed, at the alert threshold. */
function verdict(e: ExperimentSummary, alert: number): string {
  const p = e.prediction;
  if (!p) return "";
  const flagged = p.fire_risk >= alert;
  if (e.sustained && flagged) return `It kept burning, and the model would have raised an alert (score ≥ ${formatRisk(alert)}).`;
  if (e.sustained) return `It kept burning, but the model scored it below the alert threshold of ${formatRisk(alert)} — a missed fire.`;
  if (flagged) return `It went out, but the model scored it above the alert threshold of ${formatRisk(alert)} — a false alarm at this threshold.`;
  return `It went out, and the model scored it below the alert threshold of ${formatRisk(alert)} — consistent with the observation.`;
}

interface DrawerProps {
  experiment: ExperimentSummary | null;
  alert: number;
  onClose: () => void;
}

/** Side sheet with everything known about one test. Native modal <dialog>: focus trap, Esc and focus return built in. */
export function ExperimentDrawer({ experiment: e, alert, onClose }: DrawerProps) {
  const ref = useRef<HTMLDialogElement>(null);
  const detail = useApi<ExperimentDetail>(e ? `${endpoints.experiments}/${e.test_id}` : null);
  const d = detail.data?.test_id === e?.test_id ? detail.data : undefined;

  useEffect(() => {
    const dialog = ref.current;
    if (!dialog) return;
    if (e && !dialog.open) {
      dialog.showModal();
      document.documentElement.style.overflow = "hidden";
    }
    if (!e && dialog.open) dialog.close();
    if (!e) document.documentElement.style.overflow = "";
  }, [e]);

  useEffect(() => () => { document.documentElement.style.overflow = ""; }, []);

  const conditions = e ? experimentConditions(e) : null;

  return (
    <dialog
      ref={ref}
      aria-labelledby="experiment-drawer-title"
      onClose={onClose}
      onClick={(ev) => { if (ev.target === ref.current) onClose(); }}
      className="m-0 ml-auto h-dvh max-h-dvh w-full max-w-xl border-0 bg-transparent p-0 text-ink backdrop:bg-black/60 backdrop:backdrop-blur-sm
        transition-[translate] duration-300 ease-out open:translate-x-0 starting:open:translate-x-full"
    >
      {e && (
        <div className="flex h-full flex-col border-l border-white/[0.08] bg-space-900/95 shadow-2xl backdrop-blur-xl">
          <header className="flex items-start justify-between gap-4 border-b border-white/[0.06] p-5 sm:p-6">
            <div className="min-w-0 space-y-2">
              <ProvenanceBadge kind="observed" />
              <h2 id="experiment-drawer-title" className="font-display text-2xl font-bold tracking-tight">
                {testLabel(e.test_id)} <span className="font-mono text-base font-medium text-ink-3">{e.flex_identifier}</span>
              </h2>
              <p className="text-xs text-ink-3">
                {new Intl.DateTimeFormat("en-GB", { dateStyle: "long", timeStyle: "short", timeZone: "UTC" }).format(new Date(e.datetime_gmt))} UTC · ISS
              </p>
            </div>
            <button type="button" onClick={onClose} autoFocus aria-label="Close test details"
              className="rounded-lg p-2 text-ink-3 transition hover:bg-white/[0.06] hover:text-ink">
              <X className="size-5" aria-hidden="true" />
            </button>
          </header>

          <div className="flex-1 space-y-5 overflow-y-auto p-5 sm:p-6">
            <div className="flex items-center gap-3 rounded-xl border p-4"
              style={{ borderColor: `${OUTCOME_COLORS[e.outcome]}55`, background: `${OUTCOME_COLORS[e.outcome]}12` }}>
              <OutcomeShape outcome={e.outcome} className="size-4" />
              <div>
                <p className="text-sm font-semibold text-ink">{OUTCOME_LABEL[e.outcome]}</p>
                <p className="text-xs text-ink-2">{e.sustained ? "Counted as sustained burning (the flame did not put itself out)." : "The flame went out before the fuel was used up."}</p>
              </div>
            </div>

            <Section title="Test conditions" kind="observed">
              <Facts rows={[
                ["Fuel", e.fuel === "Heptane" ? "n-heptane" : "methanol"],
                ["Oxygen", `${e.oxygen_percent}%`],
                ["Nitrogen", `${e.nitrogen_percent}%`],
                ["CO₂", `${e.co2_percent}%`],
                ["Helium", `${e.he_percent}%`],
                ["Pressure", e.pressure_atm !== null ? `${e.pressure_atm.toFixed(3)} atm` : `— (${e.pressure_level})`],
                ["Initial diameter", e.droplet_diameter_mm !== null ? `${e.droplet_diameter_mm} mm` : "not reported"],
              ]} />
            </Section>

            <Section title="Measured results" kind="observed">
              {d ? (
                <Facts rows={[
                  ["Burn time", e.burn_time_s !== null ? `${e.burn_time_s} s` : "—"],
                  ["Extinction diameter", d.extinction_diameter_mm !== null ? `${d.extinction_diameter_mm} mm` : "—"],
                  ["Burning rate K", d.burning_rate_mm2_s !== null ? `${d.burning_rate_mm2_s} mm²/s` : "—"],
                ]} />
              ) : detail.error ? (
                <p className="text-xs text-risk-high">{detail.error.message}</p>
              ) : (
                <LoadingState rows={1} label="Loading measurements" />
              )}
            </Section>

            <Section title="Model check" kind="prediction">
              {e.prediction ? (
                <div className="space-y-3">
                  <div className="flex flex-wrap items-center gap-3">
                    <span className="font-display text-4xl font-bold tabular-nums text-ink">{formatRisk(e.prediction.fire_risk)}</span>
                    <RiskBadge level={e.prediction.risk_level} />
                  </div>
                  <p className="text-sm text-ink-2">{verdict(e, alert)}</p>
                  <p className="flex gap-2 text-xs text-ink-3">
                    <Info className="mt-0.5 size-3.5 shrink-0" aria-hidden="true" />
                    {e.prediction.method}. A single test cannot validate or refute the model.
                  </p>
                </div>
              ) : (
                <p className="text-sm text-ink-3">Not modelled: this test is outside the model&apos;s scope (see the notes below).</p>
              )}
            </Section>

            {d && d.notes.length > 0 && (
              <Section title="Data-quality notes">
                <ul className="space-y-2">
                  {d.notes.map((n) => (
                    <li key={n} className="flex gap-2 text-sm text-ink-2">
                      <Info className="mt-0.5 size-4 shrink-0 text-risk-elevated" aria-hidden="true" />{n}
                    </li>
                  ))}
                </ul>
              </Section>
            )}

            {d && (
              <Section title="Source">
                <a href={d.source.url} target="_blank" rel="noreferrer" className="group flex items-start gap-2 text-sm text-ink-2 hover:text-ink">
                  <FlaskConical className="mt-0.5 size-4 shrink-0 text-prov-observed" aria-hidden="true" />
                  <span>{d.source.title}<ExternalLink className="ml-1 inline size-3 opacity-60" aria-hidden="true" /></span>
                </a>
                {d.source.doi && (
                  <a href={`https://doi.org/${d.source.doi}`} target="_blank" rel="noreferrer" className="font-mono text-xs text-plasma hover:underline">
                    doi:{d.source.doi}
                  </a>
                )}
              </Section>
            )}
          </div>

          <footer className="space-y-2.5 border-t border-white/[0.06] p-4 sm:p-5">
            {conditions && e.prediction && (
              <p className="text-[0.6875rem] text-ink-3">
                The analyzer uses the final model, trained on all tests including this one, so its score can differ slightly from the out-of-fold score above.
              </p>
            )}
            <div className="flex flex-col gap-2 sm:flex-row">
              {conditions ? (
                <>
                  <Link href={`/risk?${conditionsToQuery(conditions)}`} onClick={onClose}
                    className="inline-flex flex-1 items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-flame to-ember px-4 py-2.5 text-sm font-semibold text-space-950">
                    <ArrowUpRight className="size-4" aria-hidden="true" />Analyze these conditions
                  </Link>
                  <Link href={`/what-if?${conditionsToQuery(conditions)}`} onClick={onClose}
                    className="inline-flex flex-1 items-center justify-center gap-2 rounded-xl border border-white/10 px-4 py-2.5 text-sm font-medium text-ink-2 hover:border-white/20 hover:text-ink">
                    <SlidersHorizontal className="size-4" aria-hidden="true" />Use as What-If baseline
                  </Link>
                </>
              ) : (
                <p className="text-xs text-ink-3">These conditions are outside the model&apos;s scope, so they cannot be analysed.</p>
              )}
            </div>
          </footer>
        </div>
      )}
    </dialog>
  );
}
