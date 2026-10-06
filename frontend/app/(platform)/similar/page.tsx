import type { Metadata } from "next";

import { ComingSoon } from "@/components/common/coming-soon";

export const metadata: Metadata = { title: "Similar Experiments" };

export default function Page() {
  return (
    <ComingSoon
      eyebrow="Similar Tests"
      title="Similar Experiments"
      subtitle="Find the NASA tests closest to the conditions you describe."
      phase="Phase 12"
      endpoints={["POST /api/similar-experiments"]}
    />
  );
}
