"""Pydantic response models for all API endpoints."""

from __future__ import annotations

from pydantic import BaseModel

# --- Health / Stats / Metadata ---


class HealthResponse(BaseModel):
    status: str
    warehouse_version: str
    table_counts: dict[str, int]


class ReadyResponse(BaseModel):
    ready: bool
    database_connected: bool
    core_tables_present: bool


class StatsResponse(BaseModel):
    occupation_count: int
    geography_count: int
    source_count: int
    soc_version: str | None
    skill_count: int
    task_count: int


class MetadataResponse(BaseModel):
    soc_version: str | None
    oews_release_id: str | None
    onet_version: str | None
    projections_cycle: str | None
    last_load_timestamp: str | None


# --- Occupations ---


class SearchResult(BaseModel):
    soc_code: str
    occupation_title: str
    occupation_level: int
    occupation_level_name: str


class SearchResponse(BaseModel):
    query: str
    total: int = 0
    limit: int = 50
    offset: int = 0
    results: list[SearchResult]


class HierarchyNode(BaseModel):
    soc_code: str
    occupation_title: str
    occupation_level: int
    occupation_level_name: str
    children: list[HierarchyNode] = []


class HierarchyResponse(BaseModel):
    hierarchy: list[HierarchyNode]


class BreadcrumbItem(BaseModel):
    soc_code: str
    occupation_title: str


class OccupationProfileResponse(BaseModel):
    soc_code: str
    occupation_title: str
    occupation_level: int
    occupation_level_name: str
    parent_soc_code: str | None
    major_group_code: str | None
    minor_group_code: str | None
    broad_occupation_code: str | None
    detailed_occupation_code: str | None
    occupation_definition: str | None
    soc_version: str
    is_leaf: bool
    source_release_id: str
    breadcrumb: list[BreadcrumbItem]
    siblings: list[BreadcrumbItem]
    children: list[BreadcrumbItem]


# --- Wages ---


class WageEntry(BaseModel):
    geo_type: str
    geo_code: str
    geo_name: str
    employment_count: int | None
    mean_annual_wage: float | None
    median_annual_wage: float | None
    mean_hourly_wage: float | None
    median_hourly_wage: float | None
    p10_hourly_wage: float | None
    p25_hourly_wage: float | None
    p75_hourly_wage: float | None
    p90_hourly_wage: float | None
    source_release_id: str
    reference_period: str


class WagesResponse(BaseModel):
    soc_code: str
    geo_type: str
    total: int = 0
    limit: int = 100
    offset: int = 0
    wages: list[WageEntry]


class GeographyEntry(BaseModel):
    geo_type: str
    geo_code: str
    geo_name: str


class GeographiesResponse(BaseModel):
    geographies: list[GeographyEntry]


# --- Skills / Tasks / Similar ---


class SkillEntry(BaseModel):
    element_name: str
    element_id: str
    importance: float | None
    level: float | None


class SkillsResponse(BaseModel):
    soc_code: str
    source_version: str | None
    skills: list[SkillEntry]


class TaskEntry(BaseModel):
    task_description: str
    relevance_score: float | None
    task_id: str


class TasksResponse(BaseModel):
    soc_code: str
    source_version: str | None
    tasks: list[TaskEntry]


class SimilarEntry(BaseModel):
    soc_code: str
    occupation_title: str
    similarity_score: float


class SimilarResponse(BaseModel):
    soc_code: str
    similar: list[SimilarEntry]


# --- Knowledge / Abilities ---


class KnowledgeEntry(BaseModel):
    element_name: str
    element_id: str
    importance: float | None
    level: float | None


class KnowledgeResponse(BaseModel):
    soc_code: str
    source_version: str | None
    knowledge: list[KnowledgeEntry]


class AbilityEntry(BaseModel):
    element_name: str
    element_id: str
    importance: float | None
    level: float | None


class AbilitiesResponse(BaseModel):
    soc_code: str
    source_version: str | None
    abilities: list[AbilityEntry]


class ActivityEntry(BaseModel):
    element_name: str
    element_id: str
    importance: float | None
    level: float | None


class ActivitiesResponse(BaseModel):
    soc_code: str
    source_version: str | None
    activities: list[ActivityEntry]


class EducationCategory(BaseModel):
    category: int
    category_label: str | None
    percentage: float | None


class EducationElement(BaseModel):
    element_id: str
    element_name: str
    scale_id: str
    categories: list[EducationCategory]


class EducationResponse(BaseModel):
    soc_code: str
    source_version: str | None
    summary: str | None
    elements: list[EducationElement]


class TechnologyItem(BaseModel):
    example_name: str
    commodity_code: str | None
    commodity_title: str | None
    hot_technology: bool | None


class TechnologyGroup(BaseModel):
    t2_type: str
    items: list[TechnologyItem]


class TechnologyResponse(BaseModel):
    soc_code: str
    source_version: str | None
    groups: list[TechnologyGroup]


# --- Projections ---


class ProjectionData(BaseModel):
    projection_cycle: str
    base_year: int
    projection_year: int
    base_employment: int | None
    projected_employment: int | None
    employment_change: int | None
    percent_change: float | None
    annual_openings: int | None
    education_category: str | None
    training_category: str | None
    work_experience_category: str | None
    source_release_id: str


class ProjectionsResponse(BaseModel):
    soc_code: str
    projections: ProjectionData | None


# --- Trends ---


class TrendPoint(BaseModel):
    year: int
    value: float | None
    suppressed: bool | str | None = None
    suppression_flag: str | None = None
    source_release_id: str | None = None
    metric_name: str | None = None
    units: str | None = None
    derivation_type: str | None = None
    geo_name: str | None = None
    yoy_change: float | None = None
    yoy_pct_change: float | None = None


class TrendSeriesResponse(BaseModel):
    soc_code: str
    title: str | None = None
    metric: str
    geo_type: str | None = None
    comparability_mode: str | None = None
    series: list[TrendPoint]
    years: list[int] | None = None


class CompareOccupationEntry(BaseModel):
    soc_code: str
    title: str
    series: list[TrendPoint]


class TrendCompareResponse(BaseModel):
    metric: str
    geo_type: str
    occupations: list[CompareOccupationEntry]


class GeographyTrendEntry(BaseModel):
    geo_name: str
    geo_code: str
    value: float | None
    source_release_id: str | None = None


class TrendGeographyResponse(BaseModel):
    soc_code: str
    metric: str
    year: int | None
    geographies: list[GeographyTrendEntry]


class MoverEntry(BaseModel):
    soc_code: str
    title: str
    pct_change: float | None
    abs_change: float | None


class TrendMoversResponse(BaseModel):
    metric: str
    geo_type: str
    year: int | None
    available_years: list[int]
    gainers: list[MoverEntry]
    losers: list[MoverEntry]


class MetricEntry(BaseModel):
    metric_name: str
    units: str | None
    display_format: str | None
    derivation_type: str | None
    comparability_constraint: str | None
    description: str | None


class MetricsListResponse(BaseModel):
    metrics: list[MetricEntry]


# --- Methodology ---


class SourceEntry(BaseModel):
    name: str
    provider: str
    role: str
    url: str
    current_version: str | None
    refresh_cadence: str


class SourcesResponse(BaseModel):
    sources: list[SourceEntry]


class ValidationCheck(BaseModel):
    check: str
    passed: bool
    detail: str


class ValidationResponse(BaseModel):
    total_checks: int
    passed: int
    failed: int
    all_passed: bool
    checks: list[ValidationCheck]


# ============================================================
# CPI domain models
# ============================================================


class CpiMemberSummary(BaseModel):
    member_code: str
    title: str
    hierarchy_level: str | None = None
    semantic_role: str


class CpiSearchResponse(BaseModel):
    query: str
    total: int
    results: list[CpiMemberSummary]


class CpiMemberDetail(BaseModel):
    member_code: str
    title: str
    hierarchy_level: str | None = None
    semantic_role: str
    is_cross_cutting: bool
    has_average_price: bool
    has_relative_importance: bool
    variant_count: int = 0
    children_count: int = 0
    ancestors: list[CpiMemberSummary] = []


class CpiChildEntry(BaseModel):
    member_code: str
    title: str
    hierarchy_level: str | None = None
    semantic_role: str


class CpiChildrenResponse(BaseModel):
    member_code: str
    children: list[CpiChildEntry]


class CpiRelationEntry(BaseModel):
    member_code: str
    title: str
    relation_type: str
    description: str | None = None


class CpiRelationsResponse(BaseModel):
    member_code: str
    relations: list[CpiRelationEntry]


class CpiSeriesPoint(BaseModel):
    year: int
    period: str
    value: float


class CpiSeriesResponse(BaseModel):
    member_code: str
    title: str
    area_code: str = "0000"
    index_family: str = "CPI-U"
    seasonal_adjustment: str = "S"
    series: list[CpiSeriesPoint] = []


class CpiAreaSummary(BaseModel):
    area_code: str
    area_title: str
    area_type: str
    publication_frequency: str


class CpiAreaDetail(BaseModel):
    area_code: str
    area_title: str
    area_type: str
    publication_frequency: str
    member_count: int = 0


class CpiAreaMembersResponse(BaseModel):
    area_code: str
    members: list[CpiMemberSummary]


class CpiImportanceEntry(BaseModel):
    reference_period: str
    relative_importance: float
    area_code: str = "0000"


class CpiImportanceResponse(BaseModel):
    member_code: str
    title: str
    entries: list[CpiImportanceEntry] = []


class CpiExplorerNode(BaseModel):
    member_code: str
    title: str
    hierarchy_level: str | None = None
    relative_importance: float | None = None
    children: list[CpiExplorerNode] = []


class CpiAveragePriceEntry(BaseModel):
    year: int
    period: str
    average_price: float
    unit_description: str | None = None


class CpiAveragePriceResponse(BaseModel):
    member_code: str
    title: str
    entries: list[CpiAveragePriceEntry] = []


class CpiRevisionVintageEntry(BaseModel):
    year: int
    period: str
    vintage_label: str
    index_value: float
    is_preliminary: bool


class CpiRevisionVintageResponse(BaseModel):
    member_code: str
    title: str
    entries: list[CpiRevisionVintageEntry] = []
