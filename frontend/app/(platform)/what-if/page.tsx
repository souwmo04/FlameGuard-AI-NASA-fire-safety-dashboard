import type { Metadata } from "next";
import { Suspense } from "react";

import { LoadingState } from "@/components/ui/states";
import { WhatIfLab } from "@/components/whatif/whatif-lab";

export const metadata: Metadata = { title: "What-If Lab" };

export default function Page() {
  // Scenario A can arrive in the URL (e.g. from a NASA test), read on the client below this boundary.
  return (
    <Suspense fallback={<LoadingState rows={10} label="Loading What-If Lab" />}>
      <WhatIfLab />
    </Suspense>
  );
}
