import type { Metadata } from "next";

import { ComingSoon } from "@/components/common/coming-soon";

export const metadata: Metadata = { title: "Experiment Explorer" };

export default function Page() {
  return (
    <ComingSoon
      eyebrow="Experiments"
      title="Experiment Explorer"
      subtitle="All 274 tests from NASA’s Flame Extinguishment Experiment aboard the ISS."
      phase="Phase 10"
      endpoints={["GET /api/experiments","GET /api/experiments/{id}","GET /api/sources"]}
    />
  );
}
