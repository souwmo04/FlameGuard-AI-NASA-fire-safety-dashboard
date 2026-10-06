/**
 * Typed client for the FlameGuard FastAPI backend. All science happens on the server;
 * this module only sends requests and returns typed JSON.
 */
import type {
  Conditions,
  ConditionRankingResponse,
  DomainResponse,
  ExperimentDetail,
  ExperimentList,
  HealthResponse,
  ModelInfoResponse,
  PredictResponse,
  RankingResponse,
  SimilarResponse,
  Source,
  StatsResponse,
  SuppressantsResponse,
  WhatIfResponse,
} from "./types";

export const API_URL = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(/\/$/, "");

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number | null,
    public readonly detail?: unknown,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

type Query = Record<string, string | number | boolean | null | undefined>;

function withQuery(path: string, query?: Query): string {
  if (!query) return path;
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(query)) {
    if (value !== undefined && value !== null && value !== "") params.set(key, String(value));
  }
  const qs = params.toString();
  return qs ? `${path}?${qs}` : path;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_URL}${path}`, {
      ...init,
      headers: { Accept: "application/json", ...(init?.body ? { "Content-Type": "application/json" } : {}) },
    });
  } catch {
    throw new ApiError(`Cannot reach the FlameGuard API at ${API_URL}. Is the backend running?`, null);
  }
  if (!response.ok) {
    let detail: unknown;
    try {
      detail = await response.json();
    } catch {
      detail = undefined;
    }
    throw new ApiError(`API request failed (${response.status})`, response.status, detail);
  }
  return (await response.json()) as T;
}

export const get = <T>(path: string, query?: Query) => request<T>(withQuery(path, query));
export const post = <T>(path: string, body: unknown) =>
  request<T>(path, { method: "POST", body: JSON.stringify(body) });

/** Endpoint paths, used as SWR cache keys. */
export const endpoints = {
  health: "/api/health",
  stats: "/api/stats",
  sources: "/api/sources",
  domain: "/api/domain",
  model: "/api/model",
  experiments: "/api/experiments",
  suppressants: "/api/suppressants",
  ranking: "/api/ranking",
  conditionRanking: "/api/ranking/conditions",
} as const;

export const api = {
  health: () => get<HealthResponse>(endpoints.health),
  stats: () => get<StatsResponse>(endpoints.stats),
  sources: () => get<Source[]>(endpoints.sources),
  domain: () => get<DomainResponse>(endpoints.domain),
  model: () => get<ModelInfoResponse>(endpoints.model),
  experiments: (query?: Query) => get<ExperimentList>(endpoints.experiments, query),
  experiment: (testId: number) => get<ExperimentDetail>(`${endpoints.experiments}/${testId}`),
  ranking: (query?: Query) => get<RankingResponse>(endpoints.ranking, query),
  conditionRanking: (query?: Query) => get<ConditionRankingResponse>(endpoints.conditionRanking, query),
  suppressants: () => get<SuppressantsResponse>(endpoints.suppressants),
  predict: (conditions: Conditions) => post<PredictResponse>("/api/predict", conditions),
  whatIf: (body: { scenario_a: Conditions; scenario_b: Conditions; sweep?: "oxygen" | "droplet" | null; sweep_points?: number }) =>
    post<WhatIfResponse>("/api/what-if", body),
  similar: (body: Conditions & { k?: number }) => post<SimilarResponse>("/api/similar-experiments", body),
};
