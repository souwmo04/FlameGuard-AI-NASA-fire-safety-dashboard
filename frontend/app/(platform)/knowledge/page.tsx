import type { Metadata } from "next";

import { AskFlameGuard } from "@/components/ask/ask-flameguard";

export const metadata: Metadata = { title: "Ask FlameGuard" };

export default function Page() {
  return <AskFlameGuard />;
}
