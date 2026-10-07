"use client";

import { Search, X } from "lucide-react";
import type { Dispatch, SetStateAction } from "react";

import { OutcomeShape } from "@/components/charts/outcome-shape";
import { OUTCOME_SHORT, type Outcome } from "@/lib/chart-theme";
import { cn } from "@/lib/cn";
import {
  activeFilterCount,
  DEFAULT_FILTERS,
  type ExperimentFilters,
  type FuelFilter,
  type PressureFilter,
  type SuppressantFilter,
} from "@/lib/experiment-filters";

const chipBase = "inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1 text-xs font-medium transition";
const chipOn = "bg-flame/15 text-flame ring-1 ring-flame/30";
const chipOff = "text-ink-3 hover:bg-white/[0.04] hover:text-ink-2";

function ChipRadio<T extends string>({ label, value, options, onChange }: {
  label: string;
  value: T;
  options: { value: T; label: string }[];
  onChange: (v: T) => void;
}) {
  return (
    <div className="flex flex-wrap items-center gap-1.5">
      <span className="label-caps mr-1 w-full text-[0.625rem] sm:w-auto">{label}</span>
      <div role="radiogroup" aria-label={label} className="flex flex-wrap gap-1">
        {options.map((o) => (
          <button key={o.value} type="button" role="radio" aria-checked={value === o.value} onClick={() => onChange(o.value)}
            className={cn(chipBase, value === o.value ? chipOn : chipOff)}>
            {o.label}
          </button>
        ))}
      </div>
    </div>
  );
}

const OUTCOMES: Outcome[] = ["Extinction", "Completion", "Disruption"];

interface Props {
  value: ExperimentFilters;
  onChange: Dispatch<SetStateAction<ExperimentFilters>>;
}

/** Search box plus filter chips for the experiment table; all filtering happens in the browser. */
export function ExperimentFiltersBar({ value: f, onChange }: Props) {
  // functional updates, so quick successive changes never overwrite each other
  const set = (patch: Partial<ExperimentFilters>) => onChange((prev) => ({ ...prev, ...patch }));
  const toggleOutcome = (o: Outcome) =>
    onChange((prev) => ({ ...prev, outcomes: prev.outcomes.includes(o) ? prev.outcomes.filter((x) => x !== o) : [...prev.outcomes, o] }));
  const active = activeFilterCount(f);

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
        <label className="relative flex-1">
          <span className="sr-only">Search by FLEX identifier or test number</span>
          <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-ink-3" aria-hidden="true" />
          <input
            type="search"
            value={f.query}
            onChange={(e) => set({ query: e.target.value })}
            placeholder="Search FLEX ID (e.g. 205R001) or test number"
            className="h-10 w-full rounded-xl border border-white/[0.08] bg-white/[0.03] pl-9 pr-3 text-sm text-ink placeholder:text-ink-3 focus:border-flame/40 focus:outline-none"
          />
        </label>
        <div className="flex items-center gap-2">
          <label className={cn(chipBase, "cursor-pointer", f.scopeOnly ? chipOn : chipOff)}>
            <input type="checkbox" className="sr-only" checked={f.scopeOnly} onChange={(e) => set({ scopeOnly: e.target.checked })} />
            Used by the model
          </label>
          <label className={cn(chipBase, "cursor-pointer", f.flaggedOnly ? chipOn : chipOff)}>
            <input type="checkbox" className="sr-only" checked={f.flaggedOnly} onChange={(e) => set({ flaggedOnly: e.target.checked })} />
            Has data-quality notes
          </label>
          {active > 0 && (
            <button type="button" onClick={() => onChange(DEFAULT_FILTERS)} className={cn(chipBase, "text-ink-2 hover:text-ink")}>
              <X className="size-3.5" aria-hidden="true" />Clear {active}
            </button>
          )}
        </div>
      </div>

      <div className="grid gap-3 lg:grid-cols-2 2xl:grid-cols-4">
        <ChipRadio<FuelFilter> label="Fuel" value={f.fuel} onChange={(v) => set({ fuel: v })}
          options={[{ value: "all", label: "All" }, { value: "Methanol", label: "Methanol" }, { value: "Heptane", label: "n-Heptane" }]} />
        <ChipRadio<SuppressantFilter> label="Suppressant" value={f.suppressant} onChange={(v) => set({ suppressant: v })}
          options={[{ value: "all", label: "All" }, { value: "none", label: "None" }, { value: "CO2", label: "CO₂" }, { value: "He", label: "Helium" }]} />
        <ChipRadio<PressureFilter> label="Pressure" value={f.pressure} onChange={(v) => set({ pressure: v })}
          options={[{ value: "all", label: "All" }, { value: "1atm", label: "1 atm" }, { value: "0.7atm", label: "0.7 atm" }, { value: "2-3atm", label: "2–3 atm" }]} />
        <div className="flex flex-wrap items-center gap-1.5">
          <span className="label-caps mr-1 w-full text-[0.625rem] sm:w-auto">Outcome</span>
          <div role="group" aria-label="Outcome" className="flex flex-wrap gap-1">
            {OUTCOMES.map((o) => (
              <button key={o} type="button" aria-pressed={f.outcomes.includes(o)} onClick={() => toggleOutcome(o)}
                className={cn(chipBase, f.outcomes.includes(o) ? chipOn : chipOff)}>
                <OutcomeShape outcome={o} />{OUTCOME_SHORT[o]}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
