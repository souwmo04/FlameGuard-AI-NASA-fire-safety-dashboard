"use client";

import { AnimatePresence, motion } from "motion/react";
import { useState, type ReactNode } from "react";

import { cn } from "@/lib/cn";

import { Cite } from "./cite";

interface Part {
  id: string;
  label: string;
  x: number;
  y: number;
  body: ReactNode;
}

const PARTS: Part[] = [
  {
    id: "chamber", label: "Combustion chamber (CIR)", x: 18, y: 14,
    body: <>A 90-litre chamber in the Combustion Integrated Rack, in the ISS Destiny module. It can work from about 0 to 9 atm, but a conservative safety analysis limited FLEX to about 3 atm.<Cite p={2} to={3} /></>,
  },
  {
    id: "needles", label: "Deployment needles", x: 20, y: 50,
    body: <>Two opposed stainless-steel needles (250 µm outside diameter) dispense fuel between them, stretch the droplet, then retract rapidly to leave it floating.<Cite p={3} /><Cite p={4} /></>,
  },
  {
    id: "droplet", label: "Fuel droplet", x: 50, y: 50,
    body: <>Methanol or n-heptane droplets, initially about 2–5 mm across. The droplet is misshaped by the needle retraction but becomes spherical within about 1 s.<Cite p={2} /><Cite p={7} /></>,
  },
  {
    id: "igniters", label: "Hot-wire igniters", x: 50, y: 22,
    body: <>Two hot-wire igniters, 180° apart, are switched on for a preset time and then pulled well away from the droplet.<Cite p={4} /><Cite p={5} /></>,
  },
  {
    id: "hibms", label: "Backlit camera (HiBMs)", x: 84, y: 50,
    body: <>A backlit 1024 × 1024, 12-bit camera at about 30 frames per second, with a ~30 mm field of view, tracks the droplet’s diameter over time. Estimated uncertainty: ±50 µm.<Cite p={4} /><Cite p={8} /></>,
  },
  {
    id: "lluv", label: "UV flame camera (LLUV)", x: 50, y: 84,
    body: <>An intensified camera filtered at 310 nm images light from excited hydroxyl (OH) radicals, giving the flame diameter. Estimated uncertainty: ±200 µm.<Cite p={4} /><Cite p={9} /></>,
  },
  {
    id: "fiber", label: "Support fiber (optional)", x: 80, y: 20,
    body: <>Some droplets were held on an 80 µm fiber, either when free droplets drifted too fast or to study a slow, sub-buoyant flow by moving the fiber.<Cite p={4} /></>,
  },
];

/** Schematic of the FLEX apparatus (not to scale); each labelled part explains itself with a citation. */
export function ApparatusDiagram() {
  const [active, setActive] = useState<string>("droplet");
  const part = PARTS.find((p) => p.id === active)!;

  return (
    <div className="grid gap-5 lg:grid-cols-[minmax(0,1.1fr)_minmax(0,1fr)] lg:items-center">
      <div className="relative mx-auto aspect-square w-full max-w-md">
        <svg viewBox="0 0 100 100" className="absolute inset-0 size-full" aria-hidden="true">
          <rect x="6" y="6" width="88" height="88" rx="14" fill="rgb(255 255 255 / 0.02)" stroke="rgb(255 255 255 / 0.12)" strokeWidth="0.6" />
          {/* needles */}
          <path d="M8 50 H40" stroke="#94a3b8" strokeWidth="1.2" strokeLinecap="round" />
          <path d="M60 50 H70" stroke="#94a3b8" strokeWidth="1.2" strokeLinecap="round" strokeDasharray="1.5 1.5" />
          {/* igniters */}
          <path d="M50 10 V38 M50 62 V68" stroke="#f97316" strokeWidth="0.8" strokeLinecap="round" />
          {/* fiber */}
          <path d="M62 36 L92 14" stroke="#cbd5e1" strokeWidth="0.3" strokeDasharray="1 1" />
          {/* backlight beam -> camera */}
          <path d="M14 46 H86 M14 54 H86" stroke="#22d3ee" strokeOpacity="0.15" strokeWidth="0.5" />
          <rect x="86" y="44" width="6" height="12" rx="1.5" fill="#0e7490" />
          {/* LLUV below */}
          <rect x="44" y="86" width="12" height="6" rx="1.5" fill="#7c3aed" />
          {/* flame + droplet */}
          <motion.circle cx="50" cy="50" r="10" fill="none" stroke="#38bdf8" strokeOpacity="0.6" strokeWidth="1.2"
            animate={{ r: [9.5, 10.5, 9.5] }} transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }} />
          <circle cx="50" cy="50" r="3.2" fill="#1e293b" stroke="#e2e8f0" strokeWidth="0.6" />
        </svg>
        {PARTS.map((p) => (
          <button
            key={p.id}
            type="button"
            onClick={() => setActive(p.id)}
            aria-pressed={active === p.id}
            aria-label={p.label}
            className={cn("absolute size-6 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 transition",
              active === p.id ? "scale-110 border-flame bg-flame/30 shadow-[0_0_16px_rgb(251_191_36/0.7)]" : "border-white/40 bg-space-950/70 hover:border-flame/70")}
            style={{ left: `${p.x}%`, top: `${p.y}%` }}
          >
            <span className={cn("absolute inset-1.5 rounded-full", active === p.id ? "bg-flame" : "bg-white/50")} aria-hidden="true" />
          </button>
        ))}
        <span className="absolute bottom-2 left-1/2 -translate-x-1/2 text-[0.625rem] uppercase tracking-[0.12em] text-ink-3">Schematic · not to scale</span>
      </div>

      <div className="space-y-3">
        <div className="flex flex-wrap gap-1.5" role="group" aria-label="Apparatus parts">
          {PARTS.map((p) => (
            <button key={p.id} type="button" onClick={() => setActive(p.id)} aria-pressed={active === p.id}
              className={cn("rounded-lg px-2.5 py-1 text-xs transition", active === p.id ? "bg-flame/15 text-flame ring-1 ring-flame/30" : "text-ink-3 hover:bg-white/[0.04] hover:text-ink-2")}>
              {p.label}
            </button>
          ))}
        </div>
        <AnimatePresence mode="wait">
          <motion.div key={part.id} initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -6 }} transition={{ duration: 0.2 }}
            className="rounded-xl border border-white/[0.07] bg-white/[0.02] p-4" aria-live="polite">
            <h3 className="font-display text-base font-semibold text-ink">{part.label}</h3>
            <p className="mt-2 text-sm leading-relaxed text-ink-2">{part.body}</p>
          </motion.div>
        </AnimatePresence>
      </div>
    </div>
  );
}
