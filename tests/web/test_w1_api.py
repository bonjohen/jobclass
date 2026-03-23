"""Phase W1 tests: API foundation, health, metadata, page rendering, error handling."""

import pytest


class TestHealthEndpoint:
    """WT1-02, WT1-06: /api/health returns status, warehouse version, table counts."""

    def test_health_returns_200(self, client):
        resp = client.get("/api/health")
        assert resp.status_code == 200

    def test_health_has_required_fields(self, client):
        data = client.get("/api/health").json()
        assert "status" in data
        assert "warehouse_version" in data
        assert "table_counts" in data

    def test_health_status_ok(self, client):
        data = client.get("/api/health").json()
        assert data["status"] == "ok"

    def test_health_warehouse_version(self, client):
        data = client.get("/api/health").json()
        assert data["warehouse_version"] == "2018"

    def test_health_table_counts_nonzero(self, client):
        data = client.get("/api/health").json()
        counts = data["table_counts"]
        assert counts["dim_occupation"] > 0
        assert counts["fact_occupation_employment_wages"] > 0

    def test_health_schema_no_extra_fields(self, client):
        data = client.get("/api/health").json()
        assert set(data.keys()) == {"status", "warehouse_version", "table_counts"}


class TestMetadataEndpoint:
    """WT1-03: /api/metadata returns source versions and release IDs."""

    def test_metadata_returns_200(self, client):
        resp = client.get("/api/metadata")
        assert resp.status_code == 200

    def test_metadata_soc_version(self, client):
        data = client.get("/api/metadata").json()
        assert data["soc_version"] == "2018"

    def test_metadata_oews_release(self, client):
        data = client.get("/api/metadata").json()
        assert data["oews_release_id"] is not None

    def test_metadata_onet_version(self, client):
        data = client.get("/api/metadata").json()
        assert data["onet_version"] is not None

    def test_metadata_last_load_timestamp(self, client):
        data = client.get("/api/metadata").json()
        assert data["last_load_timestamp"] is not None


class TestLandingPage:
    """WT1-04: Base layout renders header, navigation, footer."""

    def test_landing_returns_200(self, client):
        resp = client.get("/")
        assert resp.status_code == 200

    def test_landing_has_header(self, client):
        html = client.get("/").text
        assert "<header" in html

    def test_landing_has_nav(self, client):
        html = client.get("/").text
        assert "<nav" in html

    def test_landing_has_footer(self, client):
        html = client.get("/").text
        assert "<footer" in html

    def test_landing_has_content(self, client):
        html = client.get("/").text
        assert "Labor Market Occupation Data" in html

    def test_landing_has_entry_points(self, client):
        html = client.get("/").text
        assert "Search Occupations" in html
        assert "Browse Hierarchy" in html
        assert "Methodology" in html


class TestErrorHandling:
    """WT1-05: Structured error responses."""

    def test_api_404_returns_json(self, client):
        resp = client.get("/api/nonexistent")
        assert resp.status_code == 404
        data = resp.json()
        assert "error" in data
        assert "message" in data

    def test_page_404_returns_html(self, client):
        resp = client.get("/nonexistent-page")
        assert resp.status_code == 404
        assert "Page Not Found" in resp.text

    def test_api_404_no_stack_trace(self, client):
        resp = client.get("/api/nonexistent")
        data = resp.json()
        assert "traceback" not in str(data).lower()
        assert "Traceback" not in str(data)
