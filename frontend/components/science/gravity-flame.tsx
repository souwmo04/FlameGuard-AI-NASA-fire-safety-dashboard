"use client";

import { motion, useReducedMotion } from "motion/react";
import { useState } from "react";

import { Segmented } from "@/components/risk/segmented";

type Mode = "earth" | "space";

const SHAPES = {
  // Earth: buoyancy pulls the flame up into a tall teardrop above the droplet
  earth: { outer: { rx: 46, ry: 96, cy: -44 }, inner: { rx: 30, ry: 70, cy: -30 } },
  // Microgravity: no buoyant flow, so the flame surrounds the droplet as a sphere
  space: { outer: { rx: 78, ry: 78, cy: 0 }, inner: { rx: 60, ry: 60, cy: 0 } },
} as const;

/** Illustration (not to scale, not data): a burning droplet's flame with and without gravity. */
export function GravityFlame() {
  const [mode, setMode] = useState<Mode>("space");
  const reduce = useReducedMotion();
  const s = SHAPES[mode];
  const t = reduce ? { duration: 0 } : { type: "spring" as const, stiffness: 60, damping: 14 };

  return (
    <figure className="space-y-4">
      <div className="max-w-sm">
        <Segmented<Mode> label="Gravity" value={mode} onChange={setMode}
          options={[{ value: "earth", label: "Earth (1 g)" }, { value: "space", label: "ISS (microgravity)" }]} />
      </div>
      <div className="relative mx-auto aspect-square w-full max-w-sm overflow-hidden rounded-2xl border border-white/[0.06] bg-[radial-gradient(circle_at_50%_55%,rgb(17_24_39),rgb(5_7_13))]">
        <svg viewBox="-150 -170 300 300" className="size-full" role="img"
          aria-label={mode === "earth"
            ? "Illustration: on Earth the flame around a burning droplet is pulled upward into a tall teardrop shape by buoyant flow."
            : "Illustration: in microgravity the flame surrounds the droplet as a sphere."}>
          <defs>
            <radialGradient id="gf-outer" cx="50%" cy="60%" r="60%">
              <stop offset="0%" stopColor="#fde68a" stopOpacity="0.0" />
              <stop offset="70%" stopColor="#fb923c" stopOpacity="0.35" />
              <stop offset="100%" stopColor="#f97316" stopOpacity="0.0" />
            </radialGradient>
            <radialGradient id="gf-inner" cx="50%" cy="55%" r="55%">
              <stop offset="0%" stopColor="#fbbf24" stopOpacity="0.0" />
              <stop offset="80%" stopColor="#38bdf8" stopOpacity="0.55" />
              <stop offset="100%" stopColor="#38bdf8" stopOpacity="0.0" />
            </radialGradient>
          </defs>

          {/* buoyant plume arrows (Earth only) */}
          {[-40, 0, 40].map((x, i) => (
            <motion.g key={x} animate={{ opacity: mode === "earth" ? 0.8 : 0 }} transition={{ duration: 0.4 }}>
              <motion.path d={`M${x} -60 L${x} -150 M${x - 7} -138 L${x} -152 L${x + 7} -138`} stroke="#94a3b8" strokeWidth="2" fill="none"
                strokeLinecap="round" strokeDasharray="6 8"
                animate={reduce ? undefined : { strokeDashoffset: [0, -28] }}
                transition={{ duration: 1.2, repeat: Infinity, ease: "linear", delay: i * 0.2 }} />
            </motion.g>
          ))}

          <motion.ellipse cx={0} initial={false} animate={s.outer} transition={t} fill="url(#gf-outer)" />
          <motion.ellipse cx={0} initial={false} animate={s.inner} transition={t} fill="none" stroke="url(#gf-inner)" strokeWidth="10" />
          <motion.ellipse cx={0} initial={false} animate={s.inner} transition={t} fill="none" stroke="#7dd3fc" strokeOpacity="0.5" strokeWidth="1.5" />
          {/* droplet */}
          <circle r="13" fill="#1e293b" stroke="#cbd5e1" strokeWidth="1.5" />
          <circle r="4" cx="-4" cy="-4" fill="#e2e8f0" opacity="0.6" />

          <text x="0" y="118" textAnchor="middle" fill="#7b8aa3" fontSize="10">
            {mode === "earth" ? "buoyant flow stretches the flame upward" : "no buoyant flow: a spherical flame"}
          </text>
        </svg>
        <span className="absolute left-3 top-3 rounded-md bg-space-950/70 px-2 py-0.5 text-[0.625rem] uppercase tracking-[0.12em] text-ink-3">
          Illustration · not to scale
        </span>
      </div>
    </figure>
  );
}
