"""FastAPI application for the JobClass reporting website."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from jobclass.web.api.health import router as health_router
from jobclass.web.api.methodology import router as methodology_router
from jobclass.web.api.metrics import MetricsMiddleware
from jobclass.web.api.metrics import router as metrics_router
from jobclass.web.api.occupations import router as occupations_router
from jobclass.web.api.projections import router as projections_router
from jobclass.web.api.skills import router as skills_router
from jobclass.web.api.trends import router as trends_router
from jobclass.web.api.wages import router as wages_router

_WEB_DIR = Path(__file__).parent
_TEMPLATES_DIR = _WEB_DIR / "templates"
_STATIC_DIR = _WEB_DIR / "static"


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="JobClass — Labor Market Reporting",
        description="Occupation-centric analytical reporting website",
        version="1.0.0",
    )

    # Security middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["GET"],
        allow_headers=["*"],
    )

    class CSPMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request: Request, call_next) -> Response:
            response = await call_next(request)
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'"
            )
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            return response

    app.add_middleware(CSPMiddleware)
    app.add_middleware(MetricsMiddleware)

    # Mount static files
    if _STATIC_DIR.exists():
        app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")

    # Register API routers
    app.include_router(health_router)
    app.include_router(metrics_router)
    app.include_router(occupations_router)
    app.include_router(wages_router)
    app.include_router(skills_router)
    app.include_router(projections_router)
    app.include_router(methodology_router)
    app.include_router(trends_router)

    # Template engine
    templates = Jinja2Templates(directory=str(_TEMPLATES_DIR))

    # --- Page routes ---

    @app.get("/", response_class=HTMLResponse)
    async def landing(request: Request):
        return templates.TemplateResponse(
            request,
            "base.html",
            {
                "page_title": "JobClass — Labor Market Reporting",
                "content_template": "landing.html",
            },
        )

    @app.get("/search", response_class=HTMLResponse)
    async def search_page(request: Request):
        return templates.TemplateResponse(
            request,
            "base.html",
            {
                "page_title": "Search Occupations — JobClass",
                "content_template": "search.html",
            },
        )

    @app.get("/hierarchy", response_class=HTMLResponse)
    async def hierarchy_page(request: Request):
        return templates.TemplateResponse(
            request,
            "base.html",
            {
                "page_title": "Occupation Hierarchy — JobClass",
                "content_template": "hierarchy.html",
            },
        )

    @app.get("/occupation/{soc_code}", response_class=HTMLResponse)
    async def occupation_page(request: Request, soc_code: str):
        return templates.TemplateResponse(
            request,
            "base.html",
            {
                "page_title": f"{soc_code} — JobClass",
                "content_template": "occupation.html",
                "soc_code": soc_code,
            },
        )

    @app.get("/methodology", response_class=HTMLResponse)
    async def methodology_page(request: Request):
        return templates.TemplateResponse(
            request,
            "base.html",
            {
                "page_title": "Methodology — JobClass",
                "content_template": "methodology.html",
            },
        )

    @app.get("/occupation/{soc_code}/wages", response_class=HTMLResponse)
    async def wages_comparison_page(request: Request, soc_code: str):
        return templates.TemplateResponse(
            request,
            "base.html",
            {
                "page_title": f"Wages by State — {soc_code} — JobClass",
                "content_template": "wages_comparison.html",
                "soc_code": soc_code,
            },
        )

    @app.get("/lessons", response_class=HTMLResponse)
    async def lessons_landing(request: Request):
        return templates.TemplateResponse(
            request,
            "base.html",
            {
                "page_title": "Lessons — JobClass",
                "content_template": "lessons.html",
            },
        )

    @app.get("/lessons/{lesson_slug}", response_class=HTMLResponse)
    async def lesson_page(request: Request, lesson_slug: str):
        valid_slugs = {
            "federal-data": ("The Federal Labor Data Landscape", "lessons_federal_data.html"),
            "dimensional-modeling": (
                "Dimensional Modeling for Labor Data",
                "lessons_dimensional_modeling.html",
            ),
            "multi-vintage": ("The Multi-Vintage Challenge", "lessons_multi_vintage.html"),
            "data-quality": (
                "Data Quality Traps in Government Sources",
                "lessons_data_quality.html",
            ),
            "time-series": ("Time-Series Normalization", "lessons_time_series.html"),
            "idempotent-pipelines": ("Idempotent Pipeline Design", "lessons_idempotent_pipelines.html"),
            "static-site": ("Static Site Generation", "lessons_static_site.html"),
            "testing-deployment": ("Testing and Deployment", "lessons_testing_deployment.html"),
            "similarity-algorithms": (
                "Choosing the Right Similarity Algorithm",
                "lessons_similarity.html",
            ),
            "thread-safety": (
                "Thread-Safe Database Connections",
                "lessons_thread_safety.html",
            ),
            "multi-vintage-queries": (
                "Multi-Vintage Query Pitfalls",
                "lessons_multi_vintage_queries.html",
            ),
            "ui-data-alignment": (
                "UI-Data Alignment",
                "lessons_ui_data_alignment.html",
            ),
        }
        if lesson_slug not in valid_slugs:
            return templates.TemplateResponse(
                request,
                "404.html",
                {"page_title": "Page Not Found"},
                status_code=404,
            )
        title, template_name = valid_slugs[lesson_slug]
        return templates.TemplateResponse(
            request,
            "base.html",
            {
                "page_title": f"{title} — Lessons — JobClass",
                "content_template": template_name,
            },
        )

    @app.get("/trends", response_class=HTMLResponse)
    async def trends_landing(request: Request):
        return templates.TemplateResponse(
            request,
            "base.html",
            {
                "page_title": "Trends — JobClass",
                "content_template": "trends.html",
            },
        )

    @app.get("/trends/explorer/{soc_code}", response_class=HTMLResponse)
    async def trend_explorer_page(request: Request, soc_code: str):
        return templates.TemplateResponse(
            request,
            "base.html",
            {
                "page_title": f"Trend Explorer — {soc_code} — JobClass",
                "content_template": "trend_explorer.html",
                "soc_code": soc_code,
            },
        )

    @app.get("/trends/compare", response_class=HTMLResponse)
    async def occupation_comparison_page(request: Request):
        return templates.TemplateResponse(
            request,
            "base.html",
            {
                "page_title": "Compare Occupations — JobClass",
                "content_template": "occupation_comparison.html",
            },
        )

    @app.get("/trends/geography/{soc_code}", response_class=HTMLResponse)
    async def geography_comparison_page(request: Request, soc_code: str):
        return templates.TemplateResponse(
            request,
            "base.html",
            {
                "page_title": f"Geography Comparison — {soc_code} — JobClass",
                "content_template": "geography_comparison.html",
                "soc_code": soc_code,
            },
        )

    @app.get("/trends/movers", response_class=HTMLResponse)
    async def ranked_movers_page(request: Request):
        return templates.TemplateResponse(
            request,
            "base.html",
            {
                "page_title": "Ranked Movers — JobClass",
                "content_template": "ranked_movers.html",
            },
        )

    # --- Error handlers ---

    @app.exception_handler(404)
    async def not_found_handler(request: Request, exc):
        if request.url.path.startswith("/api/"):
            return JSONResponse(
                status_code=404,
                content={"error": "not_found", "message": f"Resource not found: {request.url.path}"},
            )
        return templates.TemplateResponse(
            request,
            "404.html",
            {"page_title": "Page Not Found"},
            status_code=404,
        )

    @app.exception_handler(500)
    async def server_error_handler(request: Request, exc):
        if request.url.path.startswith("/api/"):
            return JSONResponse(
                status_code=500,
                content={"error": "internal_error", "message": "An internal error occurred"},
            )
        return templates.TemplateResponse(
            request,
            "500.html",
            {"page_title": "Server Error"},
            status_code=500,
        )

    return app


app = create_app()
