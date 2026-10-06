import type { Metadata } from "next";

import { ComingSoon } from "@/components/common/coming-soon";

export const metadata: Metadata = { title: "Suppressant Lab" };

export default function Page() {
  return (
    <ComingSoon
      eyebrow="Suppressant Lab"
      title="Suppressant Lab"
      subtitle="Nitrogen, CO₂ and helium compared using observed tests only — and an honest verdict on what the data supports."
      phase="Phase 11"
      endpoints={["GET /api/suppressants"]}
    />
  );
}
