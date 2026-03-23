"""Phase CR4 tests: pagination, accessibility, health probes, metrics, constants."""

import pytest


class TestSearchPagination:
    """CR4-01/04: Search endpoint pagination."""

    def test_search_default_pagination(self, client):
        resp = client.get("/api/occupations/search?q=15")
        data = resp.json()
        assert "total" in data
        assert "limit" in data
        assert "offset" in data
        assert data["limit"] == 50
        assert data["offset"] == 0

    def test_search_custom_limit(self, client):
        resp = client.get("/api/occupations/search?q=15&limit=2")
        data = resp.json()
        assert data["limit"] == 2
        assert len(data["results"]) <= 2

    def test_search_custom_offset(self, client):
        resp = client.get("/api/occupations/search?q=15&limit=1&offset=0")
        first = resp.json()
        resp2 = client.get("/api/occupations/search?q=15&limit=1&offset=1")
        second = resp2.json()
        if first["total"] > 1:
            assert first["results"][0]["soc_code"] != second["results"][0]["soc_code"]

    def test_search_total_exceeds_limit(self, client):
        resp = client.get("/api/occupations/search?q=15&limit=1")
        data = resp.json()
        assert data["total"] >= len(data["results"])


class TestWagesPagination:
    """CR4-02/03/04: Wages endpoint pagination."""

    def test_wages_default_pagination(self, client):
        resp = client.get("/api/occupations/15-1252/wages?geo_type=national")
        data = resp.json()
        assert "total" in data
        assert "limit" in data
        assert "offset" in data
        assert data["limit"] == 100

    def test_wages_custom_limit(self, client):
        resp = client.get("/api/occupations/15-1252/wages?geo_type=state&limit=1")
        data = resp.json()
        assert data["limit"] == 1
        assert len(data["wages"]) <= 1

    def test_wages_pagination_metadata(self, client):
        resp = client.get("/api/occupations/15-1252/wages?geo_type=state")
        data = resp.json()
        assert data["total"] >= len(data["wages"])


class TestAccessibility:
    """CR4-05/06/07/08/09: Accessibility improvements."""

    def test_occupation_sections_have_aria_live(self, client):
        resp = client.get("/occupation/15-1252")
        html = resp.text
        assert 'aria-live="polite"' in html
        assert 'aria-busy="true"' in html
        for section_id in ["wages-section", "skills-section", "tasks-section", "projections-section", "similar-section"]:
            assert section_id in html

    def test_wages_comparison_has_aria_live(self, client):
        resp = client.get("/occupation/15-1252/wages")
        html = resp.text
        assert 'aria-live="polite"' in html
        assert 'aria-busy="true"' in html

    def test_search_autocomplete_value(self, client):
        resp = client.get("/search")
        assert 'autocomplete="search"' in resp.text

    def test_hierarchy_tree_has_role(self, client):
        resp = client.get("/hierarchy")
        assert 'role="tree"' in resp.text

    def test_hierarchy_js_has_keyboard_handlers(self, client):
        resp = client.get("/static/js/hierarchy.js")
        text = resp.text
        assert "ArrowDown" in text
        assert "ArrowUp" in text
        assert "ArrowRight" in text
        assert "ArrowLeft" in text
        assert "keydown" in text


class TestFetchTimeouts:
    """CR4-10/11/12: Fetch timeouts and error UI."""

    def test_occupation_js_has_timeout(self, client):
        resp = client.get("/static/js/occupation.js")
        text = resp.text
        assert "FETCH_TIMEOUT_MS" in text
        assert "AbortController" in text
        assert "10000" in text

    def test_search_js_has_timeout(self, client):
        resp = client.get("/static/js/search.js")
        text = resp.text
        assert "FETCH_TIMEOUT_MS" in text
        assert "10000" in text

    def test_wages_js_has_timeout(self, client):
        resp = client.get("/static/js/wages.js")
        text = resp.text
        assert "FETCH_TIMEOUT_MS" in text
        assert "AbortController" in text

    def test_hierarchy_js_has_timeout(self, client):
        resp = client.get("/static/js/hierarchy.js")
        text = resp.text
        assert "FETCH_TIMEOUT_MS" in text
        assert "fetchWithTimeout" in text

    def test_landing_js_has_timeout(self, client):
        resp = client.get("/static/js/landing.js")
        text = resp.text
        assert "FETCH_TIMEOUT_MS" in text
        assert "fetchWithTimeout" in text

    def test_methodology_js_has_timeout(self, client):
        resp = client.get("/static/js/methodology.js")
        text = resp.text
        assert "FETCH_TIMEOUT_MS" in text

    def test_occupation_js_has_error_ui(self, client):
        resp = client.get("/static/js/occupation.js")
        text = resp.text
        assert "error-message" in text
        assert "Failed to load" in text

    def test_wages_js_has_error_ui(self, client):
        resp = client.get("/static/js/wages.js")
        assert "error-message" in resp.text

    def test_hierarchy_js_has_error_ui(self, client):
        resp = client.get("/static/js/hierarchy.js")
        assert "error-message" in resp.text


class TestStaticCacheBusting:
    """CR4-13: Static asset cache-busting."""

    def test_css_has_version_param(self, client):
        resp = client.get("/")
        assert "main.css?v=" in resp.text

    def test_js_has_version_param(self, client):
        resp = client.get("/")
        assert "main.js?v=" in resp.text


class TestHealthAndReady:
    """CR4-14/15/16/17: Enhanced health endpoint and readiness probe."""

    def test_health_returns_ok(self, client):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"

    def test_health_has_table_counts(self, client):
        resp = client.get("/api/health")
        data = resp.json()
        assert "dim_occupation" in data["table_counts"]
        assert "fact_occupation_employment_wages" in data["table_counts"]

    def test_ready_returns_200(self, client):
        resp = client.get("/api/ready")
        assert resp.status_code == 200
        data = resp.json()
        assert data["ready"] is True
        assert data["database_connected"] is True
        assert data["core_tables_present"] is True

    def test_ready_response_schema(self, client):
        from jobclass.web.api.models import ReadyResponse
        resp = client.get("/api/ready")
        ReadyResponse(**resp.json())


class TestMetrics:
    """CR4-22/23/24: Prometheus metrics endpoint."""

    def test_metrics_endpoint_exists(self, client):
        resp = client.get("/metrics")
        assert resp.status_code == 200

    def test_metrics_content_type(self, client):
        resp = client.get("/metrics")
        assert "text/plain" in resp.headers.get("content-type", "")

    def test_metrics_contains_counters(self, client):
        # Make a request first to generate metrics
        client.get("/api/health")
        resp = client.get("/metrics")
        text = resp.text
        assert "jobclass_http_requests_total" in text

    def test_metrics_contains_histograms(self, client):
        client.get("/api/health")
        resp = client.get("/metrics")
        assert "jobclass_http_request_duration_seconds" in resp.text


class TestDriftThresholdConstants:
    """CR4-25: Hardcoded drift thresholds extracted to named constants."""

    def test_row_count_shift_uses_constant(self):
        from jobclass.validate.framework import ROW_COUNT_SHIFT_THRESHOLD_PCT
        assert ROW_COUNT_SHIFT_THRESHOLD_PCT == 20.0

    def test_material_delta_uses_constant(self):
        from jobclass.validate.framework import MATERIAL_DELTA_THRESHOLD_PCT
        assert MATERIAL_DELTA_THRESHOLD_PCT == 15.0

    def test_detect_row_count_shift_default(self):
        from jobclass.validate.framework import detect_row_count_shift
        # 25% shift should fail at 20% threshold
        result = detect_row_count_shift(100, 125)
        assert result.passed is False

    def test_classify_material_delta_default(self):
        from jobclass.validate.framework import classify_material_delta
        report = classify_material_delta(
            "test", "v1", "wages",
            {"key1": 100.0}, {"key1": 120.0},
        )
        assert report.exceeds_threshold is True

    def test_env_example_exists(self):
        from pathlib import Path
        env_example = Path(__file__).parent.parent.parent / ".env.example"
        assert env_example.exists()
        content = env_example.read_text()
        assert "JOBCLASS_DB_PATH" in content
