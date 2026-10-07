import type { Metadata } from "next";

import { SciencePage } from "@/components/science/science-page";

export const metadata: Metadata = { title: "Microgravity Science" };

export default function Page() {
  return <SciencePage />;
}
