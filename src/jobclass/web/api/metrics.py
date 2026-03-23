"""Prometheus metrics endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response as StarletteResponse

from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

router = APIRouter(tags=["metrics"])

REQUEST_COUNT = Counter(
    "jobclass_http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)

REQUEST_DURATION = Histogram(
    "jobclass_http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
)


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware that records request count and duration metrics."""

    async def dispatch(self, request: Request, call_next) -> StarletteResponse:
        import time

        # Skip metrics for the /metrics endpoint itself
        if request.url.path == "/metrics":
            return await call_next(request)

        method = request.method
        path = request.url.path

        start = time.monotonic()
        response = await call_next(request)
        duration = time.monotonic() - start

        REQUEST_COUNT.labels(method=method, endpoint=path, status=response.status_code).inc()
        REQUEST_DURATION.labels(method=method, endpoint=path).observe(duration)

        return response


@router.get("/metrics")
def metrics() -> Response:
    """Expose Prometheus-formatted metrics."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
