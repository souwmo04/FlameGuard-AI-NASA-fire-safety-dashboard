import type { Conditions, ExperimentSummary } from "./types";

/**
 * Conditions <-> URL query, so a scenario can be linked (e.g. "analyse this NASA test's conditions").
 * Only shape is checked here; the API validates ranges and returns a clear error otherwise.
 */
export function conditionsToQuery(c: Conditions): string {
  const q = new URLSearchParams({
    fuel: c.fuel,
    o2: String(c.oxygen_percent),
    supp: c.suppressant ?? "none",
    supp_pct: String(c.suppressant_percent ?? 0),
    d0: String(c.droplet_diameter_mm),
  });
  return q.toString();
}

export function conditionsFromQuery(q: URLSearchParams): Conditions | null {
  const fuel = q.get("fuel");
  const supp = q.get("supp") ?? "none";
  const o2 = Number(q.get("o2"));
  const pct = Number(q.get("supp_pct") ?? 0);
  const d0 = Number(q.get("d0"));
  if (fuel !== "Methanol" && fuel !== "Heptane") return null;
  if (supp !== "none" && supp !== "CO2" && supp !== "He") return null;
  if (![o2, pct, d0].every(Number.isFinite) || !q.get("o2") || !q.get("d0")) return null;
  return { fuel, oxygen_percent: o2, suppressant: supp, suppressant_percent: supp === "none" ? 0 : pct, droplet_diameter_mm: d0 };
}

/** The model inputs of an observed test, or null when the test is outside the model's scope. */
export function experimentConditions(e: ExperimentSummary): Conditions | null {
  if (!e.in_model_scope || e.droplet_diameter_mm === null) return null;
  const supp = e.suppressant === "CO2" || e.suppressant === "He" ? e.suppressant : "none";
  return {
    fuel: e.fuel,
    oxygen_percent: e.oxygen_percent,
    suppressant: supp,
    suppressant_percent: supp === "CO2" ? e.co2_percent : supp === "He" ? e.he_percent : 0,
    droplet_diameter_mm: e.droplet_diameter_mm,
  };
}
