import type { Metadata } from "next";

import { FireRiskAnalyzer } from "@/components/risk/fire-risk-analyzer";

export const metadata: Metadata = { title: "Fire Risk Analysis" };

export default function RiskPage() {
  return <FireRiskAnalyzer />;
}
