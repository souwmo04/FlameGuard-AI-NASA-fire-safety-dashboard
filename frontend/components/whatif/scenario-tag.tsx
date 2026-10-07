import { cn } from "@/lib/cn";

import { SCENARIO, type ScenarioKey } from "./scenario-style";

/** Small lettered chip identifying scenario A or B (letter + name, not colour alone). */
export function ScenarioTag({ which, className }: { which: ScenarioKey; className?: string }) {
  const s = SCENARIO[which];
  return (
    <span className={cn("inline-flex items-center gap-1.5 rounded-md border px-1.5 py-0.5 text-[0.6875rem] font-bold uppercase tracking-[0.12em]", s.border, s.bg, s.text, className)}>
      <span className="font-mono">{s.letter}</span>
      <span className="font-semibold text-ink-2">{s.name}</span>
    </span>
  );
}
