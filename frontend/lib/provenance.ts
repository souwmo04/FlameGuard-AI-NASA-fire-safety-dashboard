import {
  Brain,
  FlaskConical,
  Gauge,
  type LucideIcon,
  MessageSquare,
  ShieldCheck,
  Sigma,
  SlidersHorizontal,
} from "lucide-react";

import type { Provenance, RiskLevel } from "./types";

export interface ProvenanceStyle {
  label: string;
  short: string;
  description: string;
  icon: LucideIcon;
  /** Tailwind classes for text, border and tinted background */
  classes: string;
}

/** Every number shown is tagged with one of these; meaning never relies on colour alone. */
export const PROVENANCE: Record<Provenance, ProvenanceStyle> = {
  observed: {
    label: "NASA observed",
    short: "Observed",
    description: "Measured on the International Space Station in NASA's FLEX experiment.",
    icon: FlaskConical,
    classes: "text-prov-observed border-prov-observed/30 bg-prov-observed/10",
  },
  prediction: {
    label: "ML prediction",
    short: "Prediction",
    description: "Output of the trained model — not a measurement.",
    icon: Brain,
    classes: "text-prov-prediction border-prov-prediction/30 bg-prov-prediction/10",
  },
  estimate: {
    label: "Statistical estimate",
    short: "Estimate",
    description: "Summary fitted directly to observed tests, with uncertainty; no ML model.",
    icon: Sigma,
    classes: "text-prov-estimate border-prov-estimate/30 bg-prov-estimate/10",
  },
  explanation: {
    label: "Model explanation",
    short: "Explanation",
    description: "How the model used each input (Shapley values) — associations, not causes.",
    icon: Gauge,
    classes: "text-prov-explanation border-prov-explanation/30 bg-prov-explanation/10",
  },
  interpretation: {
    label: "AI interpretation",
    short: "Interpretation",
    description: "Plain-language text generated from the model's outputs.",
    icon: MessageSquare,
    classes: "text-prov-interpretation border-prov-interpretation/30 bg-prov-interpretation/10",
  },
  hypothetical: {
    label: "Hypothetical scenario",
    short: "Hypothetical",
    description: "Conditions you chose; they may never have been tested.",
    icon: SlidersHorizontal,
    classes: "text-prov-hypothetical border-prov-hypothetical/30 bg-prov-hypothetical/10",
  },
  evaluation: {
    label: "Model evaluation",
    short: "Evaluation",
    description: "Model scored on tests it never saw during training (cross-validation).",
    icon: ShieldCheck,
    classes: "text-prov-evaluation border-prov-evaluation/30 bg-prov-evaluation/10",
  },
};

export const RISK_STYLE: Record<RiskLevel, { label: string; text: string; ring: string; glow: string }> = {
  LOW: { label: "Low", text: "text-risk-low", ring: "border-risk-low/40 bg-risk-low/10", glow: "#34d399" },
  ELEVATED: {
    label: "Elevated",
    text: "text-risk-elevated",
    ring: "border-risk-elevated/40 bg-risk-elevated/10",
    glow: "#fbbf24",
  },
  HIGH: { label: "High", text: "text-risk-high", ring: "border-risk-high/40 bg-risk-high/10", glow: "#f87171" },
};
