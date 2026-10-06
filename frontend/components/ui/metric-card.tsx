"use client";

import type { LucideIcon } from "lucide-react";
import { motion } from "motion/react";
import type { ReactNode } from "react";

import { cn } from "@/lib/cn";
import type { Provenance } from "@/lib/types";

import { AnimatedNumber } from "./animated-number";
import { GlassCard } from "./glass-card";
import { ProvenanceBadge } from "./provenance-badge";

interface MetricCardProps {
  label: string;
  value: number | null;
  format?: (n: number) => string;
  icon?: LucideIcon;
  provenance?: Provenance;
  hint?: ReactNode;
  accent?: "flame" | "plasma" | "neutral";
  className?: string;
  delay?: number;
}

const ACCENT = {
  flame: "text-flame",
  plasma: "text-plasma",
  neutral: "text-ink",
};

/** Scientific metric tile: small caps label, large animated value, provenance and a hint line. */
export function MetricCard({ label, value, format, icon: Icon, provenance, hint, accent = "neutral", className, delay = 0 }: MetricCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.45, delay, ease: [0.22, 1, 0.36, 1] }}
      whileHover={{ y: -2 }}
      className={className}
    >
      <GlassCard className="flex h-full flex-col gap-3 p-5">
        <div className="flex items-center justify-between gap-3">
          <span className="label-caps">{label}</span>
          {Icon && <Icon className={cn("size-4", ACCENT[accent])} aria-hidden="true" />}
        </div>
        <div className={cn("font-display text-4xl font-semibold tabular-nums tracking-tight", ACCENT[accent])}>
          {value === null ? <span className="text-ink-3">—</span> : <AnimatedNumber value={value} format={format} />}
        </div>
        {(hint || provenance) && (
          <div className="mt-auto flex flex-wrap items-center gap-2 text-xs text-ink-2">
            {provenance && <ProvenanceBadge kind={provenance} compact />}
            {hint}
          </div>
        )}
      </GlassCard>
    </motion.div>
  );
}
