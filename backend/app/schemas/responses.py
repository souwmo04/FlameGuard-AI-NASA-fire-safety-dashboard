"""Response models for every endpoint."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.common import Conditions, Fuel, Provenance, RiskLevel, SourceRef

# --- health / stats / sources / domain -------------------------------------------


class HealthResponse(BaseModel):
    status: Literal["ok"]
    api_version: str
    model: str
    training_tests: int
    data_sha256: str


class ExperimentCounts(BaseModel):
    total: int = Field(description="All FLEX tests in NASA PSI-69")
    in_model_scope: int = Field(description="Tests used to train the model (0.7-1 atm, complete inputs)")
    extinction: int
    completion: int
    disruption: int
    sustained: int = Field(description="Completion + disruption")


class ModelSummary(BaseModel):
    provenance: Provenance = Provenance.EVALUATION
    name: str
    validation: str
    roc_auc: float
    roc_auc_sd: float
    pr_auc: float
    brier: float
    recall_at_alert: float
    precision_at_alert: float
    calibration_slope_min: float
    calibration_slope_max: float
    alert_threshold_score: float


class StatsResponse(BaseModel):
    provenance: Provenance = Provenance.OBSERVED
    program: str
    nasa_investigations: int
    nasa_sources: int
    experiments: ExperimentCounts
    fuels: list[str]
    suppressants_tested: list[str]
    pressure_levels: list[str]
    date_start: str
    date_end: str
    model: ModelSummary


class Source(BaseModel):
    id: str
    title: str
    kind: Literal["dataset", "report"]
    publisher: str
    url: str
    doi: str | None
    license: str | None
    citation: str
    used_for: str


class FuelDomain(BaseModel):
    oxygen_percent: tuple[float, float]
    co2_percent: tuple[float, float]
    he_percent: tuple[float, float]
    droplet_diameter_mm: tuple[float, float]


class DomainResponse(BaseModel):
    fuels: dict[Fuel, FuelDomain]
    pressure_scope_atm: tuple[float, float]
    notes: list[str]


# --- experiments -----------------------------------------------------------------


class OutOfFoldPrediction(BaseModel):
    provenance: Provenance = Provenance.PREDICTION
    method: str = "Out-of-fold: predicted by models that never saw this test (mean of 5 CV repeats)"
    fire_risk: float
    risk_level: RiskLevel
    sustained_probability: float


class ExperimentSummary(BaseModel):
    provenance: Provenance = Provenance.OBSERVED
    test_id: int
    flex_identifier: str
    datetime_gmt: str
    fuel: Fuel
    pressure_atm: float | None
    pressure_level: str
    oxygen_percent: float
    nitrogen_percent: float
    co2_percent: float
    he_percent: float
    suppressant: str
    droplet_diameter_mm: float | None
    outcome: Literal["Extinction", "Completion", "Disruption"]
    sustained: bool
    burn_time_s: float | None
    qc_flags: list[str]
    in_model_scope: bool
    prediction: OutOfFoldPrediction | None
    source_id: str


class ExperimentDetail(ExperimentSummary):
    extinction_diameter_mm: float | None
    burning_rate_mm2_s: float | None
    source: SourceRef
    notes: list[str]


class ExperimentList(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[ExperimentSummary]


# --- prediction --------------------------------------------------------------------


class Contribution(BaseModel):
    key: Literal["fuel", "atmosphere", "droplet_size"]
    label: str
    impact: float = Field(description="Fire Risk points relative to the average FLEX test")
    direction: Literal["raises", "lowers", "neutral"]


class Explanation(BaseModel):
    provenance: Provenance = Provenance.EXPLANATION
    method: str
    base_value: float = Field(description="Average Fire Risk over the training tests")
    contributions: list[Contribution]
    note: str


class BandEvidence(BaseModel):
    provenance: Provenance = Provenance.EVALUATION
    level: RiskLevel
    tests: int
    observed_sustained_rate: float
    ci_low: float
    ci_high: float


class Evidence(BaseModel):
    in_tested_range: bool
    supported_by_data: bool = Field(description="Close to a tested FLEX condition (not an extrapolation)")
    nearest_tested_distance: float
    support_radius: float
    warnings: list[str]
    band: BandEvidence
    nearest_experiment_ids: list[int]


class InterpretationPoint(BaseModel):
    kind: Literal["summary", "drivers", "evidence", "extrapolation", "suppressant", "disclaimer"]
    text: str


class Interpretation(BaseModel):
    provenance: Provenance = Provenance.INTERPRETATION
    method: str = "Fixed template filled from the model outputs (no language model)"
    text: str = Field(description="All points joined into one paragraph")
    points: list[InterpretationPoint] = Field(description="The same text split into labelled statements")


class PredictResponse(BaseModel):
    provenance: Provenance = Provenance.PREDICTION
    conditions: Conditions
    fire_risk: float
    risk_level: RiskLevel
    sustained_probability: float
    extinction_probability: float
    evidence: Evidence
    explanation: Explanation
    interpretation: Interpretation
    model: str
    scope: str


# --- what-if -----------------------------------------------------------------------


class ScenarioResult(BaseModel):
    provenance: Provenance = Provenance.PREDICTION
    conditions: Conditions
    fire_risk: float
    risk_level: RiskLevel
    sustained_probability: float
    supported_by_data: bool
    in_tested_range: bool
    warnings: list[str]


class PathStep(BaseModel):
    step: str
    change: str
    fire_risk: float
    delta: float
    risk_level: RiskLevel
    supported: bool


class SweepPoint(BaseModel):
    x: float
    a: float | None
    b: float | None
    a_supported: bool
    b_supported: bool


class Sweep(BaseModel):
    feature: Literal["oxygen", "droplet"]
    label: str
    unit: str
    points: list[SweepPoint]


class WhatIfResponse(BaseModel):
    provenance: Provenance = Provenance.HYPOTHETICAL
    a: ScenarioResult
    b: ScenarioResult
    delta: float
    path: list[PathStep]
    sweep: Sweep | None
    notes: list[str]


# --- ranking -------------------------------------------------------------------------


class RankingItem(BaseModel):
    rank: int
    value: float
    experiment: ExperimentSummary


class RankingResponse(BaseModel):
    by: str
    metric_label: str
    provenance: Provenance
    method: str
    items: list[RankingItem]


class ConditionRank(BaseModel):
    rank: int
    fuel: Fuel
    pressure_level: str
    suppressant: str
    oxygen_percent: float
    co2_percent: float
    he_percent: float
    tests: int
    sustained: int
    observed_rate: float
    ci_low: float
    ci_high: float
    test_ids: list[int]


class ConditionRankingResponse(BaseModel):
    provenance: Provenance = Provenance.OBSERVED
    method: str
    items: list[ConditionRank]


# --- suppressants ----------------------------------------------------------------------


class ObservedPoint(BaseModel):
    test_id: int
    fuel: Fuel
    pressure_level: str
    suppressant: str
    oxygen_percent: float
    co2_percent: float
    he_percent: float
    droplet_diameter_mm: float | None
    outcome: str
    sustained: bool


class SeriesEstimate(BaseModel):
    provenance: Provenance = Provenance.ESTIMATE
    fuel: Fuel
    pressure_level: str
    suppressant: str
    tests: int
    sustained: int
    extinguished: int
    oxygen_tested_min: float
    oxygen_tested_max: float
    estimable: bool
    o2_50_percent: float | None
    ci_low_percent: float | None
    ci_high_percent: float | None
    ci_beyond_tested: bool
    suppressant_percent_at_o2_50: float | None
    status: str


class SeriesComparison(BaseModel):
    fuel: Fuel
    pressure_level: str
    suppressants: list[str]
    intervals_overlap: bool
    statement: str


class SuppressantsResponse(BaseModel):
    observed_provenance: Provenance = Provenance.OBSERVED
    estimate_provenance: Provenance = Provenance.ESTIMATE
    method: str
    observed: list[ObservedPoint]
    estimates: list[SeriesEstimate]
    comparisons: list[SeriesComparison]
    conclusion: str
    caveats: list[str]


# --- similar ---------------------------------------------------------------------------


class SimilarRequest(Conditions):
    k: int = Field(5, ge=1, le=25, description="Number of similar tests to return")


class SimilarItem(BaseModel):
    similarity: float = Field(description="0-100; 100 = identical tested condition")
    distance: float
    experiment: ExperimentSummary


class SimilarResponse(BaseModel):
    provenance: Provenance = Provenance.OBSERVED
    method: str
    query: Conditions
    support_radius: float
    items: list[SimilarItem]


# --- model card --------------------------------------------------------------------------


class MetricWithInterval(BaseModel):
    name: str
    nested_mean: float
    nested_sd: float
    pooled_estimate: float | None
    pooled_ci_low: float | None
    pooled_ci_high: float | None


class CalibrationBin(BaseModel):
    mean_predicted: float
    observed_rate: float
    ci_low: float
    ci_high: float
    tests: int


class BandRow(BaseModel):
    level: RiskLevel
    score_from: float
    score_to: float
    tests: int
    sustained: int
    observed_sustained_rate: float
    ci_low: float
    ci_high: float


class SubgroupRow(BaseModel):
    subgroup: str
    tests: int
    sustained: int
    roc_auc: float | None
    recall: float | None
    missed_fires: int
    false_alarms: int


class ImportanceRow(BaseModel):
    player: str
    mean_abs_points: float
    share: float


class ModelInfoResponse(BaseModel):
    provenance: Provenance = Provenance.EVALUATION
    name: str
    features: list[str]
    standardised_coefficients: dict[str, float]
    training_tests: int
    training_sustained: int
    validation: str
    metrics: list[MetricWithInterval]
    calibration: list[CalibrationBin]
    bands: list[BandRow]
    subgroups: list[SubgroupRow]
    global_importance: list[ImportanceRow]
    consistently_missed_test_ids: list[int]
    limitations: list[str]


# --- ask flameguard (retrieval-augmented answers) ---------------------------------------


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=500, description="A question about FLEX, the data or the model")


class Passage(BaseModel):
    n: int = Field(description="Citation number used in the answer, e.g. [2]")
    kind: Literal["nasa", "project", "live"]
    source_id: str
    source_title: str
    location: str
    section: str
    text: str
    url: str
    score: float


class KnowledgeSource(BaseModel):
    source_id: str
    title: str
    kind: Literal["nasa", "project", "live"]
    chunks: int
    url: str


class AskStatus(BaseModel):
    llm_configured: bool
    provider: str | None
    model: str | None
    retrieval: Literal["hybrid", "keyword"]
    embedding_model: str | None
    chunks: int
    sources: list[KnowledgeSource]
    per_minute_limit: int


class AskResponse(BaseModel):
    provenance: Provenance = Provenance.INTERPRETATION
    question: str
    mode: Literal["llm", "retrieval_only", "no_match"]
    answer: str | None = Field(description="Generated answer citing passages as [n]; null in retrieval-only mode")
    model: str | None
    passages: list[Passage]
    cited: list[int]
    warnings: list[str]
    note: str
