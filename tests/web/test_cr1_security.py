"""Phase CR1 tests: XSS prevention, SQL injection prevention, CORS/CSP headers, config consolidation."""


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

    def test_landing_js_uses_dom_methods(self, client):
        """Landing spotlight uses DOM methods, not innerHTML with raw API data."""
        resp = client.get("/static/js/landing.js")
        assert resp.status_code == 200
        assert "textContent" in resp.text or "createElement" in resp.text

    def test_occupation_js_escapes_lineage(self, client):
        """Occupation JS escapes source_release_id and source_version in lineage badges."""
        resp = client.get("/static/js/occupation.js")
        assert resp.status_code == 200
        assert "escapeHtml(w.source_release_id)" in resp.text
        assert "escapeHtml(data.source_version)" in resp.text

    def test_occupation_js_escapes_soc_in_href(self, client):
        """Occupation JS uses escapeAttr for soc_code in href attributes."""
        resp = client.get("/static/js/occupation.js")
        assert resp.status_code == 200
        assert "escapeAttr(" in resp.text

    def test_search_js_escapes_soc_in_href(self, client):
        resp = client.get("/static/js/search.js")
        assert resp.status_code == 200
        assert "escapeAttr(r.soc_code)" in resp.text

    def test_hierarchy_js_escapes_soc_in_href(self, client):
        resp = client.get("/static/js/hierarchy.js")
        assert resp.status_code == 200
        assert "escapeAttr(n.soc_code)" in resp.text

    def test_no_inline_script_in_search(self, client):
        """Search page uses external JS, no inline script blocks."""
        html = client.get("/search").text
        assert "function escapeHtml" not in html
        assert 'src="/static/js/search.js"' in html

    def test_no_inline_script_in_hierarchy(self, client):
        html = client.get("/hierarchy").text
        assert "function escapeHtml" not in html
        assert 'src="/static/js/hierarchy.js"' in html

    def test_no_inline_script_in_occupation(self, client):
        html = client.get("/occupation/15-1252").text
        assert "function escapeHtml" not in html
        assert 'src="/static/js/occupation.js"' in html

    def test_methodology_page_uses_external_js(self, client):
        html = client.get("/methodology").text
        assert 'src="/static/js/methodology.js"' in html

    def test_search_js_has_abort_controller(self, client):
        """Search uses AbortController to cancel in-flight requests."""
        resp = client.get("/static/js/search.js")
        assert resp.status_code == 200
        assert "AbortController" in resp.text


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

    def test_csp_no_unsafe_inline_script(self, client):
        """CSP should not allow unsafe-inline for scripts after script extraction."""
        resp = client.get("/")
        csp = resp.headers["content-security-policy"]
        assert "script-src 'self'" in csp
        assert "'unsafe-inline'" not in csp.split("script-src")[1].split(";")[0]

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


class TestInputValidation:
    """CR2-06 through CR2-10: API input validation."""

    def test_search_query_max_length(self, client):
        """Search rejects queries over 100 characters."""
        resp = client.get("/api/occupations/search?q=" + "a" * 101)
        assert resp.status_code == 422

    def test_invalid_soc_code_returns_400(self, client):
        """Invalid SOC code format returns 400."""
        resp = client.get("/api/occupations/INVALID")
        assert resp.status_code == 400

    def test_malformed_soc_code_returns_400(self, client):
        resp = client.get("/api/occupations/15-XXXX")
        assert resp.status_code == 400

    def test_empty_soc_code_wages_returns_400(self, client):
        resp = client.get("/api/occupations/abc/wages")
        assert resp.status_code == 400

    def test_invalid_geo_type_returns_400(self, client):
        resp = client.get("/api/occupations/15-1252/wages?geo_type=invalid")
        assert resp.status_code == 400

    def test_valid_geo_type_accepted(self, client):
        resp = client.get("/api/occupations/15-1252/wages?geo_type=national")
        assert resp.status_code == 200

    def test_invalid_soc_skills_returns_400(self, client):
        resp = client.get("/api/occupations/bad/skills")
        assert resp.status_code == 400

    def test_invalid_soc_tasks_returns_400(self, client):
        resp = client.get("/api/occupations/bad/tasks")
        assert resp.status_code == 400

    def test_invalid_soc_similar_returns_400(self, client):
        resp = client.get("/api/occupations/bad/similar")
        assert resp.status_code == 400

    def test_invalid_soc_projections_returns_400(self, client):
        resp = client.get("/api/occupations/bad/projections")
        assert resp.status_code == 400


class TestConfigConsolidation:
    """CR1-18 through CR1-19: database.py imports paths from settings.py."""

    def test_database_module_uses_settings_paths(self):
        from jobclass.config.database import _MIGRATIONS_DIR, DEFAULT_DB_PATH
        from jobclass.config.settings import DB_PATH, MIGRATIONS_DIR

        assert DEFAULT_DB_PATH == DB_PATH
        assert _MIGRATIONS_DIR == MIGRATIONS_DIR
