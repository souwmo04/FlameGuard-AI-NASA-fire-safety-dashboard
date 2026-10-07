/**
 * Chart styling shared by all Recharts figures.
 * Outcome colours were validated (CVD-safe, all pairs, dark surface #0b1020) and are always
 * paired with a marker shape and a legend label, so colour is never the only cue.
 */
export const OUTCOME_COLORS = {
  Extinction: "#0891b2",
  Completion: "#d97706",
  Disruption: "#db2777",
} as const;

export type Outcome = keyof typeof OUTCOME_COLORS;

export const OUTCOME_SHAPES: Record<Outcome, "circle" | "triangle" | "diamond"> = {
  Extinction: "circle",
  Completion: "triangle",
  Disruption: "diamond",
};

export const OUTCOME_LABEL: Record<Outcome, string> = {
  Extinction: "Self-extinguished",
  Completion: "Burned to completion",
  Disruption: "Droplet disrupted while burning",
};

export const OUTCOME_SHORT: Record<Outcome, string> = {
  Extinction: "Self-extinguished",
  Completion: "Completed",
  Disruption: "Disrupted",
};

export const RISK_COLORS = { LOW: "#34d399", ELEVATED: "#fbbf24", HIGH: "#f87171" } as const;

export const AXIS = {
  stroke: "rgb(255 255 255 / 0.12)",
  tick: { fill: "#7b8aa3", fontSize: 11 },
  tickLine: false,
} as const;

export const GRID = { stroke: "rgb(255 255 255 / 0.06)", strokeDasharray: "3 4" } as const;
