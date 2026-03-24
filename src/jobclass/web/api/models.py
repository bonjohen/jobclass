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
