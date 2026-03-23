"""FastAPI application for the JobClass reporting website."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from jobclass.web.api.health import router as health_router

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

    # Mount static files
    if _STATIC_DIR.exists():
        app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")

    # Register API routers
    app.include_router(health_router)

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
