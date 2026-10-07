"use client";

import type { LucideIcon } from "lucide-react";
import { motion } from "motion/react";
import { useId, useRef, type ReactNode } from "react";

import { cn } from "@/lib/cn";

export interface TabItem<T extends string> {
  value: T;
  label: string;
  icon?: LucideIcon;
}

interface TabsProps<T extends string> {
  label: string;
  value: T;
  items: TabItem<T>[];
  onChange: (value: T) => void;
  children: ReactNode;
}

/** WAI-ARIA tabs (arrow keys move between tabs) with an animated underline; renders the active panel. */
export function Tabs<T extends string>({ label, value, items, onChange, children }: TabsProps<T>) {
  const id = useId();
  const refs = useRef<(HTMLButtonElement | null)[]>([]);
  const onKeyDown = (e: React.KeyboardEvent, i: number) => {
    const step = e.key === "ArrowRight" ? 1 : e.key === "ArrowLeft" ? -1 : 0;
    const to = e.key === "Home" ? 0 : e.key === "End" ? items.length - 1 : step ? (i + step + items.length) % items.length : -1;
    if (to < 0) return;
    e.preventDefault();
    onChange(items[to].value);
    refs.current[to]?.focus();
  };
  return (
    <div className="space-y-5">
      <div role="tablist" aria-label={label} className="flex gap-1 overflow-x-auto overflow-y-hidden border-b border-white/[0.07]">
        {items.map((t, i) => {
          const active = t.value === value;
          const Icon = t.icon;
          return (
            <button
              key={t.value}
              ref={(el) => { refs.current[i] = el; }}
              id={`${id}-tab-${t.value}`}
              role="tab"
              type="button"
              aria-selected={active}
              aria-controls={`${id}-panel`}
              tabIndex={active ? 0 : -1}
              onClick={() => onChange(t.value)}
              onKeyDown={(e) => onKeyDown(e, i)}
              className={cn("relative flex shrink-0 items-center gap-2 px-3.5 pb-3 pt-1 text-sm font-medium transition",
                active ? "text-ink" : "text-ink-3 hover:text-ink-2")}
            >
              {Icon && <Icon className={cn("size-4", active && "text-flame")} aria-hidden="true" />}
              {t.label}
              {active && (
                <motion.span layoutId={`${id}-underline`} className="absolute inset-x-2 bottom-0 h-0.5 rounded-full bg-gradient-to-r from-flame to-ember"
                  transition={{ type: "spring", stiffness: 420, damping: 36 }} />
              )}
            </button>
          );
        })}
      </div>
      <div role="tabpanel" id={`${id}-panel`} aria-labelledby={`${id}-tab-${value}`} tabIndex={0} className="focus-visible:outline-none">
        {children}
      </div>
    </div>
  );
}
