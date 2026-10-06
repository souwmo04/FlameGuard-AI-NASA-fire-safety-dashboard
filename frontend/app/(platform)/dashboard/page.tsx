import type { Metadata } from "next";

import { MissionControl } from "@/components/dashboard/mission-control";

export const metadata: Metadata = { title: "Mission Control" };

export default function DashboardPage() {
  return <MissionControl />;
}
