"use client";

import useSWR from "swr";

import { api, type ApiError } from "@/lib/api";
import type { Conditions, PredictResponse } from "@/lib/types";

/** Model prediction for a set of conditions, cached per unique conditions. Pass null to skip. */
export function usePredict(conditions: Conditions | null) {
  return useSWR<PredictResponse, ApiError>(
    conditions ? ["predict", JSON.stringify(conditions)] : null,
    () => api.predict(conditions as Conditions),
    { revalidateOnFocus: false, shouldRetryOnError: false, keepPreviousData: true },
  );
}
