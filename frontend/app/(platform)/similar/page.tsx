import type { Metadata } from "next";
import { Suspense } from "react";

import { SimilarExplorer } from "@/components/similar/similar-explorer";
import { LoadingState } from "@/components/ui/states";

export const metadata: Metadata = { title: "Similar NASA Tests" };

export default function Page() {
  // Conditions can arrive in the URL (e.g. from Fire Risk), read on the client below this boundary.
  return (
    <Suspense fallback={<LoadingState rows={10} label="Loading similar tests" />}>
      <SimilarExplorer />
    </Suspense>
  );
}
