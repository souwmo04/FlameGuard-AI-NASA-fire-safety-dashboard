"use client";

import { motion, useReducedMotion } from "motion/react";
import Link from "next/link";

import { OUTCOME_COLORS, OUTCOME_LABEL, OUTCOME_SHAPES, type Outcome } from "@/lib/chart-theme";
import type { SimilarItem } from "@/lib/types";

const RINGS = [90, 75, 50, 25, 10]; // similarity levels drawn as rings (only those inside the map)
const GOLDEN = 2.399963229728653; // golden angle in radians: spreads points evenly without overlap

function Shape({ outcome, r }: { outcome: Outcome; r: number }) {
  const c = OUTCOME_COLORS[outcome];
  const s = OUTCOME_SHAPES[outcome];
  if (s === "circle") return <circle r={r} fill={c} stroke="#05070d" strokeWidth={1.5} />;
  if (s === "triangle") return <path d={`M0 ${-r * 1.15} L${r * 1.1} ${r * 0.8} L${-r * 1.1} ${r * 0.8} Z`} fill={c} stroke="#05070d" strokeWidth={1.5} />;
  return <path d={`M0 ${-r * 1.2} L${r * 1.2} 0 L0 ${r * 1.2} L${-r * 1.2} 0 Z`} fill={c} stroke="#05070d" strokeWidth={1.5} />;
}

/**
 * The query at the centre and each similar NASA test placed by its distance (radius) — the closer,
 * the more similar. Angle carries no meaning; it only keeps markers apart.
 */
export function Constellation({ items, radius, hovered, onHover }: {
  items: SimilarItem[];
  radius: number;
  hovered: number | null;
  onHover: (id: number | null) => void;
}) {
  const reduce = useReducedMotion();
  const R = 150;
  // Scale to the farthest test shown (at least the 60%-similarity distance), so markers use the whole map.
  const maxD = Math.max(-radius * Math.log(0.6), ...items.map((i) => i.distance)) * 1.15;
  const toR = (d: number) => (d / maxD) * R;

  return (
    <svg viewBox="-175 -175 350 350" className="mx-auto aspect-square w-full max-w-md" role="img"
      aria-label={`${items.length} nearest NASA tests placed by distance from your conditions; closer means more similar`}>
      <defs>
        <radialGradient id="sim-glow">
          <stop offset="0%" stopColor="#fbbf24" stopOpacity="0.35" />
          <stop offset="100%" stopColor="#fbbf24" stopOpacity="0" />
        </radialGradient>
      </defs>
      {RINGS.map((s) => {
        const r = toR(-radius * Math.log(s / 100));
        if (r > R + 4) return null;
        return (
          <g key={s}>
            <circle r={r} fill="none" stroke="rgb(255 255 255 / 0.08)" strokeDasharray="3 5" />
            <text x={4} y={-r - 4} fill="#7b8aa3" fontSize="9" fontFamily="var(--font-mono, monospace)">{s}%</text>
          </g>
        );
      })}
      <circle r={R + 6} fill="none" stroke="rgb(255 255 255 / 0.05)" />

      {items.map((item, i) => {
        const angle = -Math.PI / 2 + i * GOLDEN;
        const r = toR(item.distance);
        const x = Math.cos(angle) * r;
        const y = Math.sin(angle) * r;
        const e = item.experiment;
        const active = hovered === e.test_id;
        return (
          <g key={e.test_id}>
            <motion.line x1={0} y1={0} stroke={active ? "rgb(251 191 36 / 0.6)" : "rgb(255 255 255 / 0.07)"} strokeWidth={active ? 1.5 : 1}
              initial={reduce ? false : { x2: 0, y2: 0 }} animate={{ x2: x, y2: y }} transition={{ duration: 0.7, delay: 0.1 + i * 0.05, ease: [0.22, 1, 0.36, 1] }} />
            <motion.g
              initial={reduce ? false : { x: 0, y: 0, opacity: 0 }}
              animate={{ x, y, opacity: 1 }}
              transition={{ duration: 0.7, delay: 0.1 + i * 0.05, ease: [0.22, 1, 0.36, 1] }}
            >
              <Link href={`/experiments?test=${e.test_id}`} onMouseEnter={() => onHover(e.test_id)} onMouseLeave={() => onHover(null)}
                onFocus={() => onHover(e.test_id)} onBlur={() => onHover(null)} className="cursor-pointer outline-none"
                aria-label={`Test ${e.test_id}: ${OUTCOME_LABEL[e.outcome]}, ${Math.round(item.similarity)}% similar`}>
                {active && <circle r={13} fill="none" stroke="#fbbf24" strokeWidth={1.5} />}
                <Shape outcome={e.outcome} r={active ? 7 : 5.5} />
                <title>{`Test ${e.test_id} · ${OUTCOME_LABEL[e.outcome]} · ${Math.round(item.similarity)}% similar`}</title>
              </Link>
            </motion.g>
          </g>
        );
      })}

      <circle r={34} fill="url(#sim-glow)" />
      <motion.circle r={8} fill="#fbbf24" initial={reduce ? false : { scale: 0 }} animate={{ scale: [1, 1.15, 1] }}
        transition={{ duration: 2.4, repeat: reduce ? 0 : Infinity, ease: "easeInOut" }} />
      <text y={24} textAnchor="middle" fill="#f1f5f9" fontSize="10" fontWeight="600">your conditions</text>
    </svg>
  );
}
