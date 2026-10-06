import { cn } from "@/lib/cn";
import { PROVENANCE } from "@/lib/provenance";
import type { Provenance } from "@/lib/types";

interface ProvenanceBadgeProps {
  kind: Provenance;
  /** show the short label ("Observed") instead of the full one ("NASA observed") */
  compact?: boolean;
  className?: string;
}

/** Says what kind of number sits next to it. Icon + text, so colour is never the only signal. */
export function ProvenanceBadge({ kind, compact, className }: ProvenanceBadgeProps) {
  const p = PROVENANCE[kind];
  const Icon = p.icon;
  return (
    <span
      title={p.description}
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-[0.6875rem] font-semibold uppercase tracking-[0.12em]",
        p.classes,
        className,
      )}
    >
      <Icon className="size-3" aria-hidden="true" />
      {compact ? p.short : p.label}
    </span>
  );
}
