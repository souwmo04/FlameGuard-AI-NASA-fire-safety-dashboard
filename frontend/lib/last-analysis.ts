"use client";

import { useMemo, useSyncExternalStore } from "react";

import type { Conditions } from "./types";

/**
 * The most recent Fire Risk analysis (written by the /risk page) is kept in sessionStorage so
 * Mission Control can show it. Storage can be unavailable (private mode, blocked site data):
 * every access is guarded, and callers fall back to the reference scenario.
 */
const KEY = "flameguard:last-analysis";
const EVENT = "flameguard:last-analysis-changed";

/** Reference scenario shown until the user runs their own analysis: methanol in air, 3 mm droplet. */
export const REFERENCE_SCENARIO: Conditions = {
  fuel: "Methanol",
  oxygen_percent: 21,
  suppressant: "none",
  suppressant_percent: 0,
  droplet_diameter_mm: 3,
};

export function saveLastAnalysis(conditions: Conditions): void {
  try {
    sessionStorage.setItem(KEY, JSON.stringify(conditions));
    window.dispatchEvent(new Event(EVENT));
  } catch {
    /* storage unavailable: nothing to persist */
  }
}

function subscribe(callback: () => void) {
  window.addEventListener(EVENT, callback);
  window.addEventListener("storage", callback);
  return () => {
    window.removeEventListener(EVENT, callback);
    window.removeEventListener("storage", callback);
  };
}

function readRaw(): string | null {
  try {
    return sessionStorage.getItem(KEY);
  } catch {
    return null;
  }
}

/** Returns the user's last analysed conditions, or null if there is none. */
export function useLastAnalysis(): Conditions | null {
  const raw = useSyncExternalStore(subscribe, readRaw, () => null);
  return useMemo(() => {
    if (!raw) return null;
    try {
      return JSON.parse(raw) as Conditions;
    } catch {
      return null;
    }
  }, [raw]);
}
