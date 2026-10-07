"use client";

import { AnimatePresence, motion } from "motion/react";

import { ParameterSlider } from "@/components/risk/parameter-slider";
import { Segmented } from "@/components/risk/segmented";
import type { Conditions, DomainResponse, Fuel, Suppressant } from "@/lib/types";

type FuelRanges = DomainResponse["fuels"][string];

export const clamp = (v: number, [lo, hi]: readonly [number, number]) => Math.min(hi, Math.max(lo, v));

export const suppressantMax = (r: FuelRanges, s: Conditions["suppressant"]) =>
  s === "CO2" ? r.co2_percent[1] : s === "He" ? r.he_percent[1] : 0;

/** Switch fuel and pull every value back inside the new fuel's tested ranges. */
export function withFuel(c: Conditions, fuel: Fuel, domain?: DomainResponse): Conditions {
  const r = domain?.fuels[fuel];
  if (!r) return { ...c, fuel };
  return {
    ...c,
    fuel,
    oxygen_percent: clamp(c.oxygen_percent, r.oxygen_percent),
    droplet_diameter_mm: clamp(c.droplet_diameter_mm, r.droplet_diameter_mm),
    suppressant_percent: c.suppressant === "none" ? 0 : Math.min(c.suppressant_percent ?? 0, suppressantMax(r, c.suppressant)),
  };
}

/** Switch suppressant; a newly added one starts at 10% (or stays where it was), "none" resets to 0. */
export function withSuppressant(c: Conditions, s: Suppressant, domain?: DomainResponse): Conditions {
  if (s === "none") return { ...c, suppressant: s, suppressant_percent: 0 };
  const r = domain?.fuels[c.fuel as Fuel];
  const max = r ? suppressantMax(r, s) : 50;
  return { ...c, suppressant: s, suppressant_percent: Math.min(c.suppressant_percent || 10, max) };
}

interface ConditionsFieldsProps {
  value: Conditions;
  onChange: (next: Conditions) => void;
  domain: DomainResponse;
  accent?: "flame" | "plasma";
}

/** Fuel, oxygen, suppressant and droplet-size controls, limited to the ranges tested in NASA FLEX. */
export function ConditionsFields({ value, onChange, domain, accent = "flame" }: ConditionsFieldsProps) {
  const ranges = domain.fuels[value.fuel as Fuel];
  const update = (patch: Partial<Conditions>) => onChange({ ...value, ...patch });
  if (!ranges) return null;

  return (
    <>
      <Segmented<Fuel>
        label="Fuel"
        value={value.fuel as Fuel}
        accent={accent}
        onChange={(f) => onChange(withFuel(value, f, domain))}
        options={[{ value: "Methanol", label: "Methanol" }, { value: "Heptane", label: "n-Heptane" }]}
      />
      <ParameterSlider
        label="Oxygen"
        value={value.oxygen_percent}
        min={ranges.oxygen_percent[0]}
        max={ranges.oxygen_percent[1]}
        step={0.5}
        unit="% O₂"
        digits={1}
        note="air ≈ 21%"
        accent={accent}
        onChange={(v) => update({ oxygen_percent: v })}
      />
      <Segmented<Suppressant>
        label="Suppressant added"
        value={(value.suppressant ?? "none") as Suppressant}
        accent={accent}
        onChange={(s) => onChange(withSuppressant(value, s, domain))}
        options={[{ value: "none", label: "None" }, { value: "CO2", label: "CO₂" }, { value: "He", label: "Helium" }]}
      />
      <AnimatePresence initial={false}>
        {value.suppressant !== "none" && (
          <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: "auto" }} exit={{ opacity: 0, height: 0 }}>
            <ParameterSlider
              label={`${value.suppressant === "CO2" ? "CO₂" : "Helium"} concentration`}
              value={value.suppressant_percent ?? 0}
              min={0}
              max={suppressantMax(ranges, value.suppressant)}
              step={1}
              unit="%"
              accent={accent}
              onChange={(v) => update({ suppressant_percent: v })}
            />
          </motion.div>
        )}
      </AnimatePresence>
      <ParameterSlider
        label="Initial droplet diameter"
        value={value.droplet_diameter_mm}
        min={ranges.droplet_diameter_mm[0]}
        max={ranges.droplet_diameter_mm[1]}
        step={0.05}
        unit="mm"
        digits={2}
        accent={accent}
        onChange={(v) => update({ droplet_diameter_mm: v })}
      />
    </>
  );
}
