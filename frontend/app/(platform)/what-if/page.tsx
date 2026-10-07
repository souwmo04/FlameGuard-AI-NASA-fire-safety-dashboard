import type { Metadata } from "next";

import { WhatIfLab } from "@/components/whatif/whatif-lab";

export const metadata: Metadata = { title: "What-If Lab" };

export default function Page() {
  return <WhatIfLab />;
}
