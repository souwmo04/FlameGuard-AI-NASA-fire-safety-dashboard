import type { Metadata } from "next";

import { ComingSoon } from "@/components/common/coming-soon";

export const metadata: Metadata = { title: "Methodology" };

export default function Page() {
  return (
    <ComingSoon
      eyebrow="Methodology"
      title="Methodology"
      subtitle="Data, model, validation, decisions and limitations."
      phase="Phase 14"
      endpoints={["GET /api/model","GET /api/sources"]}
    />
  );
}
