import { Construction } from "lucide-react";

import { GlassCard } from "@/components/ui/glass-card";
import { PageHeader } from "@/components/ui/page-header";

interface ComingSoonProps {
  eyebrow: string;
  title: string;
  subtitle: string;
  phase: string;
  endpoints: string[];
}

/** Placeholder for pages built in later phases; lists the API endpoints that already power them. */
export function ComingSoon({ eyebrow, title, subtitle, phase, endpoints }: ComingSoonProps) {
  return (
    <div className="space-y-8">
      <PageHeader eyebrow={eyebrow} title={title} subtitle={subtitle} />
      <GlassCard className="flex flex-col items-start gap-4 p-6 sm:p-8">
        <span className="inline-flex items-center gap-2 rounded-full border border-flame/30 bg-flame/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.14em] text-flame">
          <Construction className="size-3.5" aria-hidden="true" /> In development · {phase}
        </span>
        <p className="max-w-xl text-sm text-ink-2">
          The backend for this page is already live. The interface arrives in {phase}.
        </p>
        <ul className="flex flex-wrap gap-2">
          {endpoints.map((e) => (
            <li key={e} className="rounded-lg border border-white/[0.08] bg-white/[0.03] px-2.5 py-1 font-mono text-xs text-plasma">
              {e}
            </li>
          ))}
        </ul>
      </GlassCard>
    </div>
  );
}
