/** Identity of each atmosphere diluent: label plus colour (always shown together with the label). */
export const SUPPRESSANT_STYLE = {
  none: { label: "N₂ only", long: "No added suppressant (nitrogen balance)", color: "#94a3b8" },
  CO2: { label: "CO₂", long: "Carbon dioxide", color: "#38bdf8" },
  He: { label: "Helium", long: "Helium", color: "#c084fc" },
} as const;

export type SuppressantKey = keyof typeof SUPPRESSANT_STYLE;

export const suppKey = (s: string): SuppressantKey => (s === "CO2" || s === "He" ? s : "none");
