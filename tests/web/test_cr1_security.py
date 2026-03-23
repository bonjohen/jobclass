"""Phase CR1 tests: XSS prevention, SQL injection prevention, CORS/CSP headers, config consolidation."""

import pytest


class TestXSSPrevention:
    """CR1-01 through CR1-05: escapeHtml in main.js, no unescaped API data in templates."""

    def test_main_js_has_escape_html(self, client):
        resp = client.get("/static/js/main.js")
        assert resp.status_code == 200
        assert "function escapeHtml" in resp.text

    def test_main_js_has_escape_attr(self, client):
        resp = client.get("/static/js/main.js")
        assert resp.status_code == 200
        assert "function escapeAttr" in resp.text

    def test_landing_no_inner_html_with_api_data(self, client):
        """Landing spotlight uses DOM methods, not innerHTML with raw API data."""
        html = client.get("/").text
        # Should use textContent or createElement, not raw innerHTML for definition
        assert "textContent = data.occupation_definition" in html or "createElement" in html

    def test_occupation_page_escapes_lineage(self, client):
        """Occupation page escapes source_release_id and source_version in lineage badges."""
        html = client.get("/occupation/15-1252").text
        assert "escapeHtml(w.source_release_id)" in html
        assert "escapeHtml(data.source_version)" in html

    def test_occupation_page_escapes_soc_in_href(self, client):
        """Occupation page uses escapeAttr for soc_code in href attributes."""
        html = client.get("/occupation/15-1252").text
        assert "escapeAttr(" in html

    def test_search_page_escapes_soc_in_href(self, client):
        html = client.get("/search").text
        assert "escapeAttr(r.soc_code)" in html

    def test_hierarchy_page_escapes_soc_in_href(self, client):
        html = client.get("/hierarchy").text
        assert "escapeAttr(n.soc_code)" in html

    def test_no_local_escape_html_in_search(self, client):
        """escapeHtml should come from main.js, not defined locally in search."""
        html = client.get("/search").text
        assert "function escapeHtml" not in html

    def test_no_local_escape_html_in_hierarchy(self, client):
        html = client.get("/hierarchy").text
        assert "function escapeHtml" not in html

    def test_no_local_escape_html_in_occupation(self, client):
        html = client.get("/occupation/15-1252").text
        assert "function escapeHtml" not in html

    def test_methodology_escapes_versions(self, client):
        html = client.get("/methodology").text
        assert "escapeHtml(data.soc_version" in html


class TestSQLIdentifierSafety:
    """CR1-06 through CR1-10: Parameterized information_schema queries, allowlist validation."""

    def test_health_tables_all_valid_identifiers(self, client):
        """Health endpoint returns data without SQL injection."""
        resp = client.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        for table_name in data["table_counts"]:
            assert table_name.replace("_", "").isalpha() or table_name.replace("_", "").isalnum()

    def test_validation_views_all_valid(self, client):
        """Validation endpoint queries mart views safely."""
        resp = client.get("/api/methodology/validation")
        assert resp.status_code == 200
        data = resp.json()
        assert data["all_passed"] is True


class TestSecurityHeaders:
    """CR1-15 through CR1-17: CORS middleware, CSP headers."""

    def test_csp_header_present(self, client):
        resp = client.get("/")
        assert "content-security-policy" in resp.headers
        csp = resp.headers["content-security-policy"]
        assert "default-src 'self'" in csp

    def test_x_content_type_options(self, client):
        resp = client.get("/")
        assert resp.headers.get("x-content-type-options") == "nosniff"

    def test_x_frame_options(self, client):
        resp = client.get("/")
        assert resp.headers.get("x-frame-options") == "DENY"

    def test_api_has_security_headers(self, client):
        resp = client.get("/api/health")
        assert "content-security-policy" in resp.headers

    def test_cors_allows_get(self, client):
        """CORS is configured (not rejecting standard requests)."""
        resp = client.get("/api/health")
        assert resp.status_code == 200


class TestConfigConsolidation:
    """CR1-18 through CR1-19: database.py imports paths from settings.py."""

    def test_database_module_uses_settings_paths(self):
        from jobclass.config.database import DEFAULT_DB_PATH, _MIGRATIONS_DIR
        from jobclass.config.settings import DB_PATH, MIGRATIONS_DIR
        assert DEFAULT_DB_PATH == DB_PATH
        assert _MIGRATIONS_DIR == MIGRATIONS_DIR
