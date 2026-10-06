import type { Metadata } from "next";

import { ComingSoon } from "@/components/common/coming-soon";

export const metadata: Metadata = { title: "Mission Control" };

export default function Page() {
  return (
    <ComingSoon
      eyebrow="Mission Control"
      title="Mission Control"
      subtitle="Microgravity Combustion Intelligence"
      phase="Phase 6"
      endpoints={["GET /api/stats","GET /api/model","GET /api/health"]}
    />
  );
}
