import { describe, expect, it } from "vitest";

import { activeFilterCount, DEFAULT_FILTERS, filterExperiments, sortExperiments } from "./experiment-filters";
import type { ExperimentSummary } from "./types";

const exp = (o: Partial<ExperimentSummary>): ExperimentSummary =>
  ({
    test_id: 1,
    flex_identifier: "X",
    datetime_gmt: "2010-01-01T00:00:00Z",
    fuel: "Methanol",
    pressure_level: "1atm",
    suppressant: "none",
    outcome: "Extinction",
    in_model_scope: true,
    qc_flags: [],
    oxygen_percent: 21,
    droplet_diameter_mm: 3,
    burn_time_s: 5,
    prediction: null,
    ...o,
  }) as unknown as ExperimentSummary;

const items = [
  exp({ test_id: 46, flex_identifier: "205R001", outcome: "Disruption", burn_time_s: 13.1 }),
  exp({ test_id: 94, flex_identifier: "C08H101", fuel: "Heptane", suppressant: "CO2", pressure_level: "0.7atm", burn_time_s: null }),
  exp({ test_id: 10, flex_identifier: "AAA", pressure_level: "2-3atm", in_model_scope: false, qc_flags: ["missing_d0"], burn_time_s: 2 }),
];

describe("filterExperiments", () => {
  it("matches FLEX identifiers and test numbers, with or without leading zeros", () => {
    expect(filterExperiments(items, { ...DEFAULT_FILTERS, query: "205r" }).map((e) => e.test_id)).toEqual([46]);
    expect(filterExperiments(items, { ...DEFAULT_FILTERS, query: "094" }).map((e) => e.test_id)).toEqual([94]);
  });

  it("combines filters", () => {
    const f = { ...DEFAULT_FILTERS, fuel: "Heptane" as const, suppressant: "CO2" as const, outcomes: ["Extinction" as const] };
    expect(filterExperiments(items, f).map((e) => e.test_id)).toEqual([94]);
    expect(filterExperiments(items, { ...DEFAULT_FILTERS, scopeOnly: true })).toHaveLength(2);
    expect(filterExperiments(items, { ...DEFAULT_FILTERS, flaggedOnly: true }).map((e) => e.test_id)).toEqual([10]);
  });

  it("counts active filters", () => {
    expect(activeFilterCount(DEFAULT_FILTERS)).toBe(0);
    expect(activeFilterCount({ ...DEFAULT_FILTERS, query: " 46 ", fuel: "Methanol", outcomes: ["Completion"] })).toBe(3);
  });
});

describe("sortExperiments", () => {
  it("sorts both ways and always puts missing values last", () => {
    expect(sortExperiments(items, { key: "burn_time", dir: "desc" }).map((e) => e.test_id)).toEqual([46, 10, 94]);
    expect(sortExperiments(items, { key: "burn_time", dir: "asc" }).map((e) => e.test_id)).toEqual([10, 46, 94]);
  });
});
