import type { Metadata } from "next";

import { ComingSoon } from "@/components/common/coming-soon";

export const metadata: Metadata = { title: "Ask FlameGuard" };

export default function Page() {
  return (
    <ComingSoon
      eyebrow="Ask FlameGuard"
      title="Ask FlameGuard"
      subtitle="Questions answered from NASA documents, with citations — never invented."
      phase="Phase 13"
      endpoints={["POST /api/chat (planned)"]}
    />
  );
}
