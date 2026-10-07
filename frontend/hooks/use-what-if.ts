"use client";

import useSWR from "swr";

import { api, type ApiError } from "@/lib/api";
import type { Conditions, WhatIfResponse } from "@/lib/types";

export type SweepFeature = "oxygen" | "droplet";

/** Two hypothetical scenarios compared by the model, with the step path and a one-input sweep. */
export function useWhatIf(a: Conditions, b: Conditions, sweep: SweepFeature) {
  return useSWR<WhatIfResponse, ApiError>(
    ["what-if", JSON.stringify(a), JSON.stringify(b), sweep],
    () => api.whatIf({ scenario_a: a, scenario_b: b, sweep, sweep_points: 61 }),
    { revalidateOnFocus: false, shouldRetryOnError: false, keepPreviousData: true },
  );
}
