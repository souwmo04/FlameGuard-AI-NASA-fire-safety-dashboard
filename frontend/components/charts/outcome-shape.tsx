import { OUTCOME_COLORS, OUTCOME_SHAPES, type Outcome } from "@/lib/chart-theme";
import { cn } from "@/lib/cn";

/** The marker used for an outcome everywhere (circle / triangle / diamond), so shape repeats the colour cue. */
export function OutcomeShape({ outcome, className }: { outcome: Outcome; className?: string }) {
  const c = OUTCOME_COLORS[outcome];
  return (
    <svg viewBox="0 0 10 10" className={cn("size-2.5 shrink-0", className)} aria-hidden="true">
      {OUTCOME_SHAPES[outcome] === "circle" && <circle cx="5" cy="5" r="4.5" fill={c} />}
      {OUTCOME_SHAPES[outcome] === "triangle" && <path d="M5 0.5 L9.5 9.5 L0.5 9.5 Z" fill={c} />}
      {OUTCOME_SHAPES[outcome] === "diamond" && <path d="M5 0 L10 5 L5 10 L0 5 Z" fill={c} />}
    </svg>
  );
}
