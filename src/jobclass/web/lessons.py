"""Canonical lesson registry — single source of truth for lesson slugs, titles, and templates."""

from __future__ import annotations

# Each entry: (slug, title, template_name)
LESSONS: list[tuple[str, str, str]] = [
    ("federal-data", "The Federal Labor Data Landscape", "lessons_federal_data.html"),
    ("dimensional-modeling", "Dimensional Modeling for Labor Data", "lessons_dimensional_modeling.html"),
    ("multi-vintage", "The Multi-Vintage Challenge", "lessons_multi_vintage.html"),
    ("data-quality", "Data Quality Traps in Government Sources", "lessons_data_quality.html"),
    ("time-series", "Time-Series Normalization", "lessons_time_series.html"),
    ("idempotent-pipelines", "Idempotent Pipeline Design", "lessons_idempotent_pipelines.html"),
    ("static-site", "Static Site Generation", "lessons_static_site.html"),
    ("testing-deployment", "Testing and Deployment", "lessons_testing_deployment.html"),
    ("similarity-algorithms", "Choosing the Right Similarity Algorithm", "lessons_similarity.html"),
    ("thread-safety", "Thread-Safe Database Connections", "lessons_thread_safety.html"),
    ("multi-vintage-queries", "Multi-Vintage Query Pitfalls", "lessons_multi_vintage_queries.html"),
    ("ui-data-alignment", "UI-Data Alignment", "lessons_ui_data_alignment.html"),
]

# Derived lookup: slug → (title, template_name)
LESSON_SLUGS: list[str] = [slug for slug, _, _ in LESSONS]
LESSON_MAP: dict[str, tuple[str, str]] = {slug: (title, tpl) for slug, title, tpl in LESSONS}
