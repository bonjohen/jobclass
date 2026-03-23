"""Phase W5 tests: Employment projections endpoint."""

import pytest


class TestProjectionsAPI:
    """WT5-01 through WT5-04: Projections endpoint tests."""

    def test_projections_returns_data(self, client):
        resp = client.get("/api/occupations/15-1252/projections")
        assert resp.status_code == 200
        data = resp.json()
        assert data["projections"] is not None

    def test_projections_has_cycle(self, client):
        data = client.get("/api/occupations/15-1252/projections").json()
        p = data["projections"]
        assert p["projection_cycle"] is not None

    def test_projections_has_employment(self, client):
        data = client.get("/api/occupations/15-1252/projections").json()
        p = data["projections"]
        assert p["base_employment"] is not None
        assert p["projected_employment"] is not None

    def test_projections_has_growth_rate(self, client):
        data = client.get("/api/occupations/15-1252/projections").json()
        p = data["projections"]
        assert p["percent_change"] is not None

    def test_projections_has_openings(self, client):
        data = client.get("/api/occupations/15-1252/projections").json()
        p = data["projections"]
        assert "annual_openings" in p

    def test_projections_has_education(self, client):
        data = client.get("/api/occupations/15-1252/projections").json()
        p = data["projections"]
        assert "education_category" in p

    def test_projections_has_lineage(self, client):
        data = client.get("/api/occupations/15-1252/projections").json()
        p = data["projections"]
        assert p["source_release_id"] is not None

    def test_projections_nonexistent_returns_null(self, client):
        """Occupation with no projections returns null projections, not error."""
        # 11-0000 is a major group, may not have projections
        resp = client.get("/api/occupations/11-0000/projections")
        assert resp.status_code == 200

    def test_projections_nonexistent_occupation_404(self, client):
        resp = client.get("/api/occupations/99-9999/projections")
        assert resp.status_code == 404
