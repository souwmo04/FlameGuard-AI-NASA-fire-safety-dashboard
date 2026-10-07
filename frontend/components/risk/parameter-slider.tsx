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
}

/** Native range input (keyboard + screen-reader friendly) styled for the dark theme. */
export function ParameterSlider({ label, value, min, max, step, unit, onChange, note, digits = 0 }: ParameterSliderProps) {
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
        className="h-2 w-full cursor-pointer appearance-none rounded-full bg-white/[0.07] accent-flame
          [&::-moz-range-thumb]:size-4 [&::-moz-range-thumb]:rounded-full [&::-moz-range-thumb]:border-2 [&::-moz-range-thumb]:border-space-950 [&::-moz-range-thumb]:bg-flame
          [&::-webkit-slider-thumb]:size-4 [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:border-2 [&::-webkit-slider-thumb]:border-space-950 [&::-webkit-slider-thumb]:bg-flame [&::-webkit-slider-thumb]:shadow-[0_0_12px_rgb(251_191_36/0.7)]"
        style={{ background: `linear-gradient(90deg, #f59e0b 0%, #fb923c ${pct}%, rgb(255 255 255 / 0.07) ${pct}%)` }}
      />
      <div className="flex justify-between font-mono text-[0.6875rem] text-ink-3">
        <span>{min.toFixed(digits)}</span>
        {note && <span className="text-ink-3">{note}</span>}
        <span>{max.toFixed(digits)}</span>
      </div>
    </div>
  );
}
