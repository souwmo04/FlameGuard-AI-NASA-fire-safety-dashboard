"use client";

import { motion, useReducedMotion } from "motion/react";

import { AnimatedNumber } from "@/components/ui/animated-number";
import { RISK_COLORS } from "@/lib/chart-theme";
import { formatRisk } from "@/lib/format";
import type { RiskLevel } from "@/lib/types";

const START = 150; // degrees, measured clockwise from 3 o'clock
const SWEEP = 240;
const CX = 130;
const CY = 128;
const R = 100;

function point(deg: number, r = R) {
  const rad = (deg * Math.PI) / 180;
  return [CX + r * Math.cos(rad), CY + r * Math.sin(rad)] as const;
}

function arc(fromScore: number, toScore: number, r = R) {
  const a0 = START + (SWEEP * fromScore) / 100;
  const a1 = START + (SWEEP * toScore) / 100;
  const [x0, y0] = point(a0, r);
  const [x1, y1] = point(a1, r);
  const large = a1 - a0 > 180 ? 1 : 0;
  return `M ${x0} ${y0} A ${r} ${r} 0 ${large} 1 ${x1} ${y1}`;
}

interface RiskGaugeProps {
  score: number | null;
  level: RiskLevel | null;
  /** alert threshold (Fire Risk points) separating LOW from ELEVATED */
  alert: number;
  dimmed?: boolean;
}

/**
 * 240° radial gauge. The dim background zones show the risk bands; the bright arc sweeps to the
 * predicted Fire Risk. Number + band word are always printed, so colour is never the only cue.
 */
export function RiskGauge({ score, level, alert, dimmed }: RiskGaugeProps) {
  const reduce = useReducedMotion();
  const color = level ? RISK_COLORS[level] : "#7b8aa3";
  const value = score ?? 0;
  const zones: [number, number, string][] = [
    [0, alert, RISK_COLORS.LOW],
    [alert, 50, RISK_COLORS.ELEVATED],
    [50, 100, RISK_COLORS.HIGH],
  ];
  const label = score === null ? "Fire Risk not yet analysed" : `Fire Risk ${formatRisk(score)} out of 100, ${level?.toLowerCase()} risk`;

  return (
    <div role="img" aria-label={label} className={`relative mx-auto w-full max-w-[22rem] transition-opacity ${dimmed ? "opacity-45" : ""}`}>
      <svg viewBox="0 0 260 220" className="w-full overflow-visible">
        <defs>
          <filter id="gauge-glow" x="-30%" y="-30%" width="160%" height="160%">
            <feGaussianBlur stdDeviation="5" result="b" />
            <feMerge><feMergeNode in="b" /><feMergeNode in="SourceGraphic" /></feMerge>
          </filter>
        </defs>
        {/* zones */}
        {zones.map(([a, b, c]) => (
          <path key={c} d={arc(a + 0.6, b - 0.6)} stroke={c} strokeOpacity={0.22} strokeWidth={14} fill="none" strokeLinecap="butt" />
        ))}
        {/* ticks */}
        {[0, alert, 50, 100].map((t) => {
          const [x0, y0] = point(START + (SWEEP * t) / 100, R - 14);
          const [x1, y1] = point(START + (SWEEP * t) / 100, R - 22);
          const [tx, ty] = point(START + (SWEEP * t) / 100, R - 34);
          return (
            <g key={t}>
              <line x1={x0} y1={y0} x2={x1} y2={y1} stroke="#7b8aa3" strokeWidth={1.2} />
              <text x={tx} y={ty} fill="#7b8aa3" fontSize="9" textAnchor="middle" dominantBaseline="middle" fontFamily="var(--font-jetbrains)">
                {Math.round(t)}
              </text>
            </g>
          );
        })}
        {/* value arc */}
        {score !== null && (
          <motion.path
            key={`${level}`}
            d={arc(0, 100)}
            stroke={color}
            strokeWidth={14}
            strokeLinecap="round"
            fill="none"
            filter="url(#gauge-glow)"
            initial={{ pathLength: reduce ? value / 100 : 0 }}
            animate={{ pathLength: Math.max(value, 0.5) / 100 }}
            transition={{ duration: reduce ? 0 : 1.1, ease: [0.22, 1, 0.36, 1] }}
          />
        )}
      </svg>
      <div className="absolute inset-x-0 top-[34%] flex flex-col items-center">
        <span className="label-caps">Fire risk</span>
        <span className="font-display text-6xl font-bold tabular-nums tracking-tight" style={{ color }}>
          {score === null ? "—" : <AnimatedNumber value={score} format={formatRisk} />}
        </span>
        <span className="font-mono text-xs text-ink-3">/ 100</span>
      </div>
    </div>
  );
}
