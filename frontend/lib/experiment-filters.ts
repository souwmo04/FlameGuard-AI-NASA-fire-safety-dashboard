import type { Outcome } from "./chart-theme";
import type { ExperimentSummary } from "./types";

export type FuelFilter = "all" | "Methanol" | "Heptane";
export type SuppressantFilter = "all" | "none" | "CO2" | "He";
export type PressureFilter = "all" | "1atm" | "0.7atm" | "2-3atm";
export type SortKey = "test_id" | "date" | "oxygen" | "droplet" | "burn_time" | "risk";

export interface ExperimentFilters {
  query: string;
  fuel: FuelFilter;
  suppressant: SuppressantFilter;
  pressure: PressureFilter;
  outcomes: Outcome[];
  scopeOnly: boolean;
  flaggedOnly: boolean;
}

export interface Sort {
  key: SortKey;
  dir: "asc" | "desc";
}

export const DEFAULT_FILTERS: ExperimentFilters = {
  query: "",
  fuel: "all",
  suppressant: "all",
  pressure: "all",
  outcomes: [],
  scopeOnly: false,
  flaggedOnly: false,
};

const SORT_VALUE: Record<SortKey, (e: ExperimentSummary) => number | string | null> = {
  test_id: (e) => e.test_id,
  date: (e) => e.datetime_gmt,
  oxygen: (e) => e.oxygen_percent,
  droplet: (e) => e.droplet_diameter_mm,
  burn_time: (e) => e.burn_time_s,
  risk: (e) => e.prediction?.fire_risk ?? null,
};

export function filterExperiments(items: ExperimentSummary[], f: ExperimentFilters): ExperimentSummary[] {
  const q = f.query.trim().toLowerCase();
  return items.filter((e) => {
    if (q && !(e.flex_identifier.toLowerCase().includes(q) || String(e.test_id) === q.replace(/^0+/, ""))) return false;
    if (f.fuel !== "all" && e.fuel !== f.fuel) return false;
    if (f.suppressant !== "all" && e.suppressant !== f.suppressant) return false;
    if (f.pressure !== "all" && e.pressure_level !== f.pressure) return false;
    if (f.outcomes.length && !f.outcomes.includes(e.outcome)) return false;
    if (f.scopeOnly && !e.in_model_scope) return false;
    if (f.flaggedOnly && e.qc_flags.length === 0) return false;
    return true;
  });
}

/** Sort with missing values always last, whatever the direction. */
export function sortExperiments(items: ExperimentSummary[], s: Sort): ExperimentSummary[] {
  const get = SORT_VALUE[s.key];
  const sign = s.dir === "asc" ? 1 : -1;
  return [...items].sort((a, b) => {
    const va = get(a);
    const vb = get(b);
    if (va === null && vb === null) return a.test_id - b.test_id;
    if (va === null) return 1;
    if (vb === null) return -1;
    if (va < vb) return -sign;
    if (va > vb) return sign;
    return a.test_id - b.test_id;
  });
}

export const activeFilterCount = (f: ExperimentFilters) =>
  (f.query.trim() ? 1 : 0) + (f.fuel !== "all" ? 1 : 0) + (f.suppressant !== "all" ? 1 : 0) + (f.pressure !== "all" ? 1 : 0) +
  (f.outcomes.length ? 1 : 0) + (f.scopeOnly ? 1 : 0) + (f.flaggedOnly ? 1 : 0);

/** Short labels for the data-quality flags (full explanations come from the API detail endpoint). */
export const QC_LABEL: Record<string, string> = {
  d_ext_without_extinction: "Extinction diameter without extinction",
  extinction_d_ext_unmeasured: "Extinction diameter not measured",
  missing_d0: "Initial diameter missing",
  duplicate_identifier: "Duplicate FLEX identifier",
  approx_burn_time: "Approximate burn time",
  missing_test_time: "Test time missing",
  pressure_invalid_zero: "Invalid pressure (0)",
  pressure_level_from_group: "Pressure level inferred",
  d_ext_gt_d0: "Extinction diameter > initial",
};
