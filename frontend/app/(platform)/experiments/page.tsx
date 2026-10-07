import type { Metadata } from "next";
import { Suspense } from "react";

import { ExperimentExplorer } from "@/components/experiments/experiment-explorer";
import { LoadingState } from "@/components/ui/states";

export const metadata: Metadata = { title: "Experiment Explorer" };

export default function Page() {
  // The explorer reads ?test= from the URL, so it renders on the client below this boundary.
  return (
    <Suspense fallback={<LoadingState rows={10} label="Loading experiments" />}>
      <ExperimentExplorer />
    </Suspense>
  );
}
