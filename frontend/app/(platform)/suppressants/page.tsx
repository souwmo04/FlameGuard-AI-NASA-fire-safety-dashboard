import type { Metadata } from "next";

import { SuppressantLab } from "@/components/suppressants/suppressant-lab";

export const metadata: Metadata = { title: "Suppressant Lab" };

export default function Page() {
  return <SuppressantLab />;
}
