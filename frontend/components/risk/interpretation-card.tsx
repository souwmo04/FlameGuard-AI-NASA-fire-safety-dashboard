"use client";

import { Check, Copy, FlaskConical, GitCompareArrows, Info, ShieldCheck, Sparkles, TriangleAlert, type LucideIcon } from "lucide-react";
import { motion, useReducedMotion } from "motion/react";
import { useState } from "react";

import { cn } from "@/lib/cn";
import type { InterpretationPoint, PredictResponse } from "@/lib/types";

const KIND: Record<InterpretationPoint["kind"], { icon: LucideIcon; label: string; tone: string }> = {
  summary: { icon: Sparkles, label: "Verdict", tone: "text-flame" },
  drivers: { icon: GitCompareArrows, label: "What drives it", tone: "text-prov-explanation" },
  evidence: { icon: ShieldCheck, label: "Track record", tone: "text-prov-evaluation" },
  extrapolation: { icon: TriangleAlert, label: "Caution", tone: "text-risk-elevated" },
  suppressant: { icon: FlaskConical, label: "Limitation", tone: "text-risk-elevated" },
  disclaimer: { icon: Info, label: "Note", tone: "text-ink-3" },
};

/** Plain-language reading of the prediction, one labelled statement at a time. */
export function InterpretationCard({ interpretation }: { interpretation: PredictResponse["interpretation"] }) {
  const reduce = useReducedMotion();
  const [copied, setCopied] = useState(false);

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(interpretation.text);
      setCopied(true);
      setTimeout(() => setCopied(false), 1800);
    } catch {
      /* clipboard unavailable (insecure context or denied) — the text stays selectable */
    }
  };

  return (
    <div className="flex h-full flex-col gap-4">
      <ul className="space-y-3">
        {interpretation.points.map((pt, i) => {
          const k = KIND[pt.kind];
          const Icon = k.icon;
          return (
            <motion.li
              key={`${pt.kind}-${i}`}
              initial={reduce ? false : { opacity: 0, x: -8, filter: "blur(4px)" }}
              animate={{ opacity: 1, x: 0, filter: "blur(0px)" }}
              transition={{ duration: 0.45, delay: 0.15 + i * 0.12 }}
              className={cn(
                "flex gap-3 rounded-xl border p-3.5",
                pt.kind === "summary" ? "border-flame/25 bg-flame/[0.05]" : "border-white/[0.06] bg-white/[0.02]",
                (pt.kind === "extrapolation" || pt.kind === "suppressant") && "border-risk-elevated/30 bg-risk-elevated/[0.05]",
              )}
            >
              <Icon className={cn("mt-0.5 size-4 shrink-0", k.tone)} aria-hidden="true" />
              <div className="min-w-0 space-y-0.5">
                <p className={cn("label-caps text-[0.625rem]", k.tone)}>{k.label}</p>
                <p className={cn("text-sm leading-relaxed", pt.kind === "summary" ? "text-ink" : "text-ink-2")}>{pt.text}</p>
              </div>
            </motion.li>
          );
        })}
      </ul>

      <footer className="mt-auto flex flex-wrap items-center justify-between gap-3 border-t border-white/[0.06] pt-3">
        <p className="text-xs text-ink-3">{interpretation.method}.</p>
        <button
          type="button"
          onClick={copy}
          className="inline-flex items-center gap-1.5 rounded-lg border border-white/10 px-2.5 py-1.5 text-xs text-ink-2 transition hover:border-white/20 hover:text-ink"
        >
          {copied ? <Check className="size-3.5 text-risk-low" aria-hidden="true" /> : <Copy className="size-3.5" aria-hidden="true" />}
          {copied ? "Copied" : "Copy summary"}
        </button>
        <span className="sr-only" aria-live="polite">{copied ? "Summary copied to clipboard" : ""}</span>
      </footer>
    </div>
  );
}
