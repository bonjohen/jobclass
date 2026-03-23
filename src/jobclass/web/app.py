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
from jobclass.web.api.occupations import router as occupations_router
from jobclass.web.api.wages import router as wages_router
from jobclass.web.api.skills import router as skills_router
from jobclass.web.api.projections import router as projections_router
from jobclass.web.api.methodology import router as methodology_router

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
                "default-src 'self'; "
                "script-src 'self'; "
                "style-src 'self' 'unsafe-inline'"
            )
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            return response

    app.add_middleware(CSPMiddleware)

    # Mount static files
    if _STATIC_DIR.exists():
        app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")

    # Register API routers
    app.include_router(health_router)
    app.include_router(occupations_router)
    app.include_router(wages_router)
    app.include_router(skills_router)
    app.include_router(projections_router)
    app.include_router(methodology_router)

    # Template engine
    templates = Jinja2Templates(directory=str(_TEMPLATES_DIR))

    # --- Page routes ---

    @app.get("/", response_class=HTMLResponse)
    async def landing(request: Request):
        return templates.TemplateResponse("base.html", {
            "request": request,
            "page_title": "JobClass — Labor Market Reporting",
            "content_template": "landing.html",
        })

    @app.get("/search", response_class=HTMLResponse)
    async def search_page(request: Request):
        return templates.TemplateResponse("base.html", {
            "request": request,
            "page_title": "Search Occupations — JobClass",
            "content_template": "search.html",
        })

    @app.get("/hierarchy", response_class=HTMLResponse)
    async def hierarchy_page(request: Request):
        return templates.TemplateResponse("base.html", {
            "request": request,
            "page_title": "Occupation Hierarchy — JobClass",
            "content_template": "hierarchy.html",
        })

    @app.get("/occupation/{soc_code}", response_class=HTMLResponse)
    async def occupation_page(request: Request, soc_code: str):
        return templates.TemplateResponse("base.html", {
            "request": request,
            "page_title": f"{soc_code} — JobClass",
            "content_template": "occupation.html",
            "soc_code": soc_code,
        })

    @app.get("/methodology", response_class=HTMLResponse)
    async def methodology_page(request: Request):
        return templates.TemplateResponse("base.html", {
            "request": request,
            "page_title": "Methodology — JobClass",
            "content_template": "methodology.html",
        })

    @app.get("/occupation/{soc_code}/wages", response_class=HTMLResponse)
    async def wages_comparison_page(request: Request, soc_code: str):
        return templates.TemplateResponse("base.html", {
            "request": request,
            "page_title": f"Wages by State — {soc_code} — JobClass",
            "content_template": "wages_comparison.html",
            "soc_code": soc_code,
        })

    # --- Error handlers ---

    @app.exception_handler(404)
    async def not_found_handler(request: Request, exc):
        if request.url.path.startswith("/api/"):
            return JSONResponse(
                status_code=404,
                content={"error": "not_found", "message": f"Resource not found: {request.url.path}"},
            )
        return templates.TemplateResponse("404.html", {
            "request": request,
            "page_title": "Page Not Found",
        }, status_code=404)

    @app.exception_handler(500)
    async def server_error_handler(request: Request, exc):
        if request.url.path.startswith("/api/"):
            return JSONResponse(
                status_code=500,
                content={"error": "internal_error", "message": "An internal error occurred"},
            )
        return templates.TemplateResponse("500.html", {
            "request": request,
            "page_title": "Server Error",
        }, status_code=500)

    return app


app = create_app()
