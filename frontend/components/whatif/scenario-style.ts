/** Scenario A and B identities, used consistently across sliders, cards, the path and the sweep chart. */
export const SCENARIO = {
  a: { letter: "A", name: "Baseline", color: "#22d3ee", accent: "plasma", text: "text-plasma", border: "border-plasma/35", bg: "bg-plasma/[0.07]", bar: "bg-plasma/70" },
  b: { letter: "B", name: "Modified", color: "#fbbf24", accent: "flame", text: "text-flame", border: "border-flame/35", bg: "bg-flame/[0.07]", bar: "bg-gradient-to-r from-flame to-ember" },
} as const;

export type ScenarioKey = keyof typeof SCENARIO;
