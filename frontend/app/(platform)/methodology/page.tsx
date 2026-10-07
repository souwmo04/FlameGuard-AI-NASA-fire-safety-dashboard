import type { Metadata } from "next";

import { MethodologyPage } from "@/components/methodology/methodology-page";

export const metadata: Metadata = { title: "Methodology" };

export default function Page() {
  return <MethodologyPage />;
}
