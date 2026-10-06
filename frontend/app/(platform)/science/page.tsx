import type { Metadata } from "next";

import { ComingSoon } from "@/components/common/coming-soon";

export const metadata: Metadata = { title: "Earth vs Microgravity" };

export default function Page() {
  return (
    <ComingSoon
      eyebrow="Microgravity Science"
      title="Earth vs Microgravity"
      subtitle="Why flames behave differently without gravity, from sourced NASA material."
      phase="Phase 13b"
      endpoints={["GET /api/sources"]}
    />
  );
}
