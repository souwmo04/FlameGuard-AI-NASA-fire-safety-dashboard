/**
 * Friendly aliases for the API types generated from the backend's OpenAPI schema
 * (lib/api-types.ts — regenerate with `npm run gen:api`, never edit by hand).
 */
import type { components } from "./api-types";

type Schemas = components["schemas"];

export type Provenance = Schemas["Provenance"];
export type RiskLevel = Schemas["RiskLevel"];
export type Fuel = Schemas["Fuel"];
export type Suppressant = Schemas["Suppressant"];
export type Conditions = Schemas["Conditions"];

export type HealthResponse = Schemas["HealthResponse"];
export type StatsResponse = Schemas["StatsResponse"];
export type Source = Schemas["Source"];
export type DomainResponse = Schemas["DomainResponse"];
export type ModelInfoResponse = Schemas["ModelInfoResponse"];

export type ExperimentSummary = Schemas["ExperimentSummary"];
export type ExperimentDetail = Schemas["ExperimentDetail"];
export type ExperimentList = Schemas["ExperimentList"];

export type PredictResponse = Schemas["PredictResponse"];
export type Contribution = Schemas["Contribution"];
export type Explanation = Schemas["Explanation"];
export type InterpretationPoint = Schemas["InterpretationPoint"];
export type WhatIfResponse = Schemas["WhatIfResponse"];
export type RankingResponse = Schemas["RankingResponse"];
export type ConditionRankingResponse = Schemas["ConditionRankingResponse"];
export type SuppressantsResponse = Schemas["SuppressantsResponse"];
export type SimilarResponse = Schemas["SimilarResponse"];

export type RankingItem = Schemas["RankingItem"];
export type ConditionRank = Schemas["ConditionRank"];
export type SeriesEstimate = Schemas["SeriesEstimate"];
export type SeriesComparison = Schemas["SeriesComparison"];
export type SuppressantObservation = Schemas["ObservedPoint"];
export type SimilarItem = Schemas["SimilarItem"];
