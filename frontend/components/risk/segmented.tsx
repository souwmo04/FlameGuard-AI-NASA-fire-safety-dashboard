"use client";

import { motion } from "motion/react";
import { useId, useRef } from "react";

import { cn } from "@/lib/cn";

interface Option<T extends string> {
  value: T;
  label: string;
}

interface SegmentedProps<T extends string> {
  label: string;
  value: T;
  options: Option<T>[];
  onChange: (value: T) => void;
  accent?: "flame" | "plasma";
}

/** Accessible segmented control (radio group with roving focus and arrow-key navigation). */
export function Segmented<T extends string>({ label, value, options, onChange, accent = "flame" }: SegmentedProps<T>) {
  const id = useId();
  const refs = useRef<(HTMLButtonElement | null)[]>([]);

  const onKeyDown = (e: React.KeyboardEvent, index: number) => {
    const delta = e.key === "ArrowRight" || e.key === "ArrowDown" ? 1 : e.key === "ArrowLeft" || e.key === "ArrowUp" ? -1 : 0;
    if (!delta) return;
    e.preventDefault();
    const next = (index + delta + options.length) % options.length;
    onChange(options[next].value);
    refs.current[next]?.focus();
  };

  return (
    <div className="space-y-2">
      <span id={id} className="label-caps block">{label}</span>
      <div role="radiogroup" aria-labelledby={id} className="relative grid rounded-xl border border-white/[0.08] bg-white/[0.02] p-1"
        style={{ gridTemplateColumns: `repeat(${options.length}, minmax(0, 1fr))` }}>
        {options.map((o, i) => {
          const active = o.value === value;
          return (
            <button
              key={o.value}
              ref={(el) => { refs.current[i] = el; }}
              type="button"
              role="radio"
              aria-checked={active}
              tabIndex={active ? 0 : -1}
              onClick={() => onChange(o.value)}
              onKeyDown={(e) => onKeyDown(e, i)}
              className={cn("relative z-10 rounded-lg px-2 py-2 text-sm font-medium transition", active ? "text-space-950" : "text-ink-2 hover:text-ink")}
            >
              {active && (
                <motion.span layoutId={`${id}-thumb`} className={cn("absolute inset-0 -z-10 rounded-lg bg-gradient-to-r",
                  accent === "flame" ? "from-flame to-ember" : "from-[#0891b2] to-plasma")}
                  transition={{ type: "spring", stiffness: 420, damping: 34 }} />
              )}
              {o.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}
