"use client";

import { motion } from "motion/react";
import type { ReactNode } from "react";

import { GlassCard } from "@/components/ui/glass-card";
import { ProvenanceBadge } from "@/components/ui/provenance-badge";
import { cn } from "@/lib/cn";
import type { Provenance } from "@/lib/types";

interface PanelProps {
  title: string;
  provenance?: Provenance;
  description?: ReactNode;
  actions?: ReactNode;
  children: ReactNode;
  className?: string;
  delay?: number;
}

/** Titled dashboard panel with provenance label; fades up on entrance. */
export function Panel({ title, provenance, description, actions, children, className, delay = 0 }: PanelProps) {
  return (
    <motion.section
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay, ease: [0.22, 1, 0.36, 1] }}
      className={cn("min-w-0", className)}
      aria-label={title}
    >
      <GlassCard className="flex h-full flex-col gap-4 p-5 sm:p-6">
        <header className="flex flex-wrap items-start justify-between gap-3">
          <div className="space-y-1.5">
            <h2 className="font-display text-base font-semibold tracking-tight text-ink">{title}</h2>
            {description && <p className="text-xs text-ink-3">{description}</p>}
          </div>
          <div className="flex min-w-0 max-w-full flex-wrap items-center gap-2">
            {actions}
            {provenance && <ProvenanceBadge kind={provenance} compact />}
          </div>
        </header>
        <div className="min-w-0 flex-1">{children}</div>
      </GlassCard>
    </motion.section>
  );
}
