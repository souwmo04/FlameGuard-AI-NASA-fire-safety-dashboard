import type { Metadata } from "next";
import { Suspense } from "react";

import { FireRiskAnalyzer } from "@/components/risk/fire-risk-analyzer";
import { LoadingState } from "@/components/ui/states";

export const metadata: Metadata = { title: "Fire Risk Analysis" };

export default function RiskPage() {
  // Conditions can arrive in the URL (e.g. from a NASA test), read on the client below this boundary.
  return (
    <Suspense fallback={<LoadingState rows={10} label="Loading analyzer" />}>
      <FireRiskAnalyzer />
    </Suspense>
  );
}
