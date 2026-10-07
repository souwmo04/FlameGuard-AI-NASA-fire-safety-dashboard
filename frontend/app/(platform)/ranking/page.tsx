import type { Metadata } from "next";

import { RankingView } from "@/components/ranking/ranking-view";

export const metadata: Metadata = { title: "Risk Ranking" };

export default function Page() {
  return <RankingView />;
}
