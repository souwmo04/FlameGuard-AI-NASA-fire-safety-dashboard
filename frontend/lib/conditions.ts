import type { Conditions } from "./types";

/** Short human-readable description of a set of conditions. */
export function describeConditions(c: Conditions): string {
  const fuel = c.fuel === "Heptane" ? "n-heptane" : "methanol";
  const supp =
    c.suppressant === "none" || !c.suppressant ? "no added suppressant" : `${c.suppressant_percent}% ${c.suppressant === "CO2" ? "CO₂" : "He"}`;
  return `${fuel} · ${c.oxygen_percent}% O₂ · ${supp} · ${c.droplet_diameter_mm} mm droplet`;
}
