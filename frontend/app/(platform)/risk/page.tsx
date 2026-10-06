import type { Metadata } from "next";

import { ComingSoon } from "@/components/common/coming-soon";

export const metadata: Metadata = { title: "Fire Risk Analysis" };

export default function Page() {
  return (
    <ComingSoon
      eyebrow="Fire Risk"
      title="Fire Risk Analysis"
      subtitle="Set the conditions of a burning fuel droplet and see whether the model expects it to keep burning — with the evidence behind the number."
      phase="Phases 7–8"
      endpoints={["GET /api/domain","POST /api/predict"]}
    />
  );
}
