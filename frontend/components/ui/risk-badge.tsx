import { CircleCheck, Flame, TriangleAlert } from "lucide-react";

import { cn } from "@/lib/cn";
import { RISK_STYLE } from "@/lib/provenance";
import type { RiskLevel } from "@/lib/types";

const ICONS = { LOW: CircleCheck, ELEVATED: TriangleAlert, HIGH: Flame } as const;

/** Risk band with icon + word + colour (never colour alone). */
export function RiskBadge({ level, className }: { level: RiskLevel; className?: string }) {
  const style = RISK_STYLE[level];
  const Icon = ICONS[level];
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-bold uppercase tracking-[0.14em]",
        style.ring,
        style.text,
        className,
      )}
    >
      <Icon className="size-3.5" aria-hidden="true" />
      {level} risk
    </span>
  );
}
