"use client";

import useSWR, { type SWRConfiguration } from "swr";

import { ApiError, get } from "@/lib/api";

/**
 * Cached GET against the FlameGuard API. The path is the cache key, so components that ask for
 * the same data share one request. Pass `null` to skip fetching.
 */
export function useApi<T>(path: string | null, config?: SWRConfiguration<T, ApiError>) {
  return useSWR<T, ApiError>(path, (p: string) => get<T>(p), {
    revalidateOnFocus: false,
    shouldRetryOnError: false,
    ...config,
  });
}
