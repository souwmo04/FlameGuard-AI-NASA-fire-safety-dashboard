import { describe, expect, it } from "vitest";

import { conditionsFromQuery, conditionsToQuery, experimentConditions } from "./scenario-url";
import type { Conditions, ExperimentSummary } from "./types";

const methanol: Conditions = {
  fuel: "Methanol",
  oxygen_percent: 21,
  suppressant: "CO2",
  suppressant_percent: 15,
  droplet_diameter_mm: 2.78,
};

describe("scenario URLs", () => {
  it("round-trips conditions through the query string", () => {
    const q = new URLSearchParams(conditionsToQuery(methanol));
    expect(conditionsFromQuery(q)).toEqual(methanol);
  });

  it("rejects unknown fuels, suppressants and missing or invalid numbers", () => {
    expect(conditionsFromQuery(new URLSearchParams("fuel=Decane&o2=21&d0=3"))).toBeNull();
    expect(conditionsFromQuery(new URLSearchParams("fuel=Methanol&o2=21&d0=3&supp=SF6"))).toBeNull();
    expect(conditionsFromQuery(new URLSearchParams("fuel=Methanol&d0=3"))).toBeNull();
    expect(conditionsFromQuery(new URLSearchParams("fuel=Methanol&o2=abc&d0=3"))).toBeNull();
  });

  it("forces the suppressant amount to 0 when there is no suppressant", () => {
    const c = conditionsFromQuery(new URLSearchParams("fuel=Heptane&o2=18&supp=none&supp_pct=40&d0=2"));
    expect(c?.suppressant_percent).toBe(0);
  });
});

describe("experimentConditions", () => {
  const base = {
    fuel: "Heptane",
    oxygen_percent: 18,
    co2_percent: 0,
    he_percent: 15,
    suppressant: "He",
    droplet_diameter_mm: 3.1,
    in_model_scope: true,
  } as unknown as ExperimentSummary;

  it("maps an observed test to model inputs", () => {
    expect(experimentConditions(base)).toEqual({
      fuel: "Heptane",
      oxygen_percent: 18,
      suppressant: "He",
      suppressant_percent: 15,
      droplet_diameter_mm: 3.1,
    });
  });

  it("returns null outside the model's scope or without a droplet size", () => {
    expect(experimentConditions({ ...base, in_model_scope: false })).toBeNull();
    expect(experimentConditions({ ...base, droplet_diameter_mm: null })).toBeNull();
  });
});
