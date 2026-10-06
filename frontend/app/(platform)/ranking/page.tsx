import type { Metadata } from "next";

import { ComingSoon } from "@/components/common/coming-soon";

export const metadata: Metadata = { title: "Fire Risk Ranking" };

export default function Page() {
  return (
    <ComingSoon
      eyebrow="Ranking"
      title="Fire Risk Ranking"
      subtitle="Which tests the model rates highest and lowest, and which tested conditions kept flames burning most often."
      phase="Phase 11"
      endpoints={["GET /api/ranking","GET /api/ranking/conditions"]}
    />
  );
}
