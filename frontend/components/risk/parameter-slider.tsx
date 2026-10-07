"use client";

import { useId } from "react";

interface ParameterSliderProps {
  label: string;
  value: number;
  min: number;
  max: number;
  step: number;
  unit: string;
  onChange: (value: number) => void;
  /** e.g. "Tested: 12–34 %" */
  note?: string;
  digits?: number;
  /** track/thumb colour; defaults to the flame accent */
  accent?: "flame" | "plasma";
}

const ACCENT = {
  flame: { from: "#f59e0b", to: "#fb923c", thumb: "#fbbf24", glow: "rgb(251 191 36 / 0.7)" },
  plasma: { from: "#0891b2", to: "#22d3ee", thumb: "#22d3ee", glow: "rgb(34 211 238 / 0.7)" },
} as const;

/** Native range input (keyboard + screen-reader friendly) styled for the dark theme. */
export function ParameterSlider({ label, value, min, max, step, unit, onChange, note, digits = 0, accent = "flame" }: ParameterSliderProps) {
  const a = ACCENT[accent];
  const id = useId();
  const pct = ((value - min) / (max - min)) * 100;
  const text = `${value.toFixed(digits)} ${unit}`;
  return (
    <div className="space-y-2.5">
      <div className="flex items-baseline justify-between gap-3">
        <label htmlFor={id} className="label-caps">{label}</label>
        <output htmlFor={id} className="font-mono text-lg font-semibold tabular-nums text-ink">
          {value.toFixed(digits)}<span className="ml-1 text-xs text-ink-3">{unit}</span>
        </output>
      </div>
      <input
        id={id}
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        aria-valuetext={text}
        onChange={(e) => onChange(Number(e.target.value))}
        className="h-2 w-full cursor-pointer appearance-none rounded-full bg-white/[0.07] 
          [&::-moz-range-thumb]:size-4 [&::-moz-range-thumb]:rounded-full [&::-moz-range-thumb]:border-2 [&::-moz-range-thumb]:border-space-950 [&::-moz-range-thumb]:bg-[var(--thumb)]
          [&::-webkit-slider-thumb]:size-4 [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:border-2 [&::-webkit-slider-thumb]:border-space-950 [&::-webkit-slider-thumb]:bg-[var(--thumb)] [&::-webkit-slider-thumb]:shadow-[0_0_12px_var(--glow)]"
        style={{
          background: `linear-gradient(90deg, ${a.from} 0%, ${a.to} ${pct}%, rgb(255 255 255 / 0.07) ${pct}%)`,
          ["--thumb" as string]: a.thumb,
          ["--glow" as string]: a.glow,
        }}
      />
      <div className="flex justify-between font-mono text-[0.6875rem] text-ink-3">
        <span>{min.toFixed(digits)}</span>
        {note && <span className="text-ink-3">{note}</span>}
        <span>{max.toFixed(digits)}</span>
      </div>
    </div>
  );
}
