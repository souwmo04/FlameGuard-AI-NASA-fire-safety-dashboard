import type { Metadata } from "next";

import { ComingSoon } from "@/components/common/coming-soon";

export const metadata: Metadata = { title: "What-If Lab" };

export default function Page() {
  return (
    <ComingSoon
      eyebrow="What-If Lab"
      title="What-If Lab"
      subtitle="Explore how changing combustion conditions influences predicted fire behaviour."
      phase="Phase 9"
      endpoints={["POST /api/what-if"]}
    />
  );
}
