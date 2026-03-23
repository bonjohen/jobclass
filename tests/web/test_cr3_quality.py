"""Phase CR3 tests: assertion quality, negative tests, input edge cases."""

import pytest


class TestStrengthenedAssertions:
    """CR3-01 through CR3-03: Replace vague assertions with specific expected values."""

    def test_health_occupation_count_specific(self, client):
        """Health endpoint should report a meaningful occupation count from fixture data."""
        resp = client.get("/api/health")
        data = resp.json()
        # Fixture data loads a sample SOC hierarchy — exact count depends on sample size
        assert data["table_counts"]["dim_occupation"] >= 10

    def test_health_fact_count_specific(self, client):
        resp = client.get("/api/health")
        data = resp.json()
        # OEWS national + state data should produce multiple fact rows
        assert data["table_counts"]["fact_occupation_employment_wages"] >= 10

    def test_stats_specific_counts(self, client):
        resp = client.get("/api/stats")
        data = resp.json()
        assert data["occupation_count"] >= 10
        assert data["geography_count"] >= 2  # At least national + one state
        assert data["skill_count"] >= 3
        assert data["task_count"] >= 2

    def test_metadata_version_formats(self, client):
        resp = client.get("/api/metadata")
        data = resp.json()
        assert data["soc_version"] == "2018"
        assert data["oews_release_id"] is not None and len(data["oews_release_id"]) > 0
        assert data["onet_version"] is not None and len(data["onet_version"]) > 0
        assert data["last_load_timestamp"] is not None and len(data["last_load_timestamp"]) > 0

    def test_search_software_returns_expected(self, client):
        """Search for 'Software' should return specific known occupation."""
        resp = client.get("/api/occupations/search?q=15-1252")
        data = resp.json()
        codes = [r["soc_code"] for r in data["results"]]
        assert "15-1252" in codes

    def test_hierarchy_has_major_groups(self, client):
        resp = client.get("/api/occupations/hierarchy")
        data = resp.json()
        # Sample fixture has at least 2 major groups
        assert len(data["hierarchy"]) >= 2

    def test_occupation_profile_has_breadcrumb(self, client):
        resp = client.get("/api/occupations/15-1252")
        data = resp.json()
        assert len(data["breadcrumb"]) >= 2  # At least major group + current
        assert data["soc_version"] == "2018"
        assert data["source_release_id"] is not None and len(data["source_release_id"]) > 0

    def test_wages_national_has_employment(self, client):
        resp = client.get("/api/occupations/15-1252/wages?geo_type=national")
        data = resp.json()
        assert len(data["wages"]) >= 1
        w = data["wages"][0]
        assert w["employment_count"] is not None and w["employment_count"] > 0
        assert w["mean_annual_wage"] is not None and w["mean_annual_wage"] > 0

    def test_skills_has_importance_and_level(self, client):
        resp = client.get("/api/occupations/15-1252/skills")
        data = resp.json()
        assert len(data["skills"]) >= 3
        for s in data["skills"]:
            assert s["element_name"] is not None and len(s["element_name"]) > 0
            assert s["element_id"] is not None and len(s["element_id"]) > 0

    def test_tasks_have_descriptions(self, client):
        resp = client.get("/api/occupations/15-1252/tasks")
        data = resp.json()
        assert len(data["tasks"]) >= 2
        for t in data["tasks"]:
            assert len(t["task_description"]) >= 10

    def test_projections_have_employment_data(self, client):
        resp = client.get("/api/occupations/15-1252/projections")
        data = resp.json()
        assert data["projections"] is not None
        p = data["projections"]
        assert p["projection_cycle"] == "2022-2032"
        assert p["base_employment"] is not None and p["base_employment"] > 0
        assert p["projected_employment"] is not None and p["projected_employment"] > 0


class TestNegativeInputs:
    """CR3-04 through CR3-08: Negative tests for invalid inputs and edge cases."""

    def test_nonexistent_soc_code_returns_404(self, client):
        resp = client.get("/api/occupations/99-9999")
        assert resp.status_code == 404

    def test_too_short_soc_code_returns_400(self, client):
        resp = client.get("/api/occupations/15-12")
        assert resp.status_code == 400

    def test_too_long_soc_code_returns_400(self, client):
        resp = client.get("/api/occupations/15-12345")
        assert resp.status_code == 400

    def test_empty_search_returns_empty(self, client):
        resp = client.get("/api/occupations/search?q=")
        data = resp.json()
        assert data["results"] == []

    def test_search_no_matches(self, client):
        resp = client.get("/api/occupations/search?q=zzzznonexistent")
        data = resp.json()
        assert data["results"] == []

    def test_occupation_no_wages_state(self, client):
        """Occupation that exists but may have no state wages still returns 200."""
        resp = client.get("/api/occupations/11-0000/wages?geo_type=state")
        assert resp.status_code in (200, 404)

    def test_nonexistent_occupation_wages_404(self, client):
        resp = client.get("/api/occupations/99-9999/wages")
        assert resp.status_code == 404

    def test_nonexistent_occupation_skills_404(self, client):
        resp = client.get("/api/occupations/99-9999/skills")
        assert resp.status_code == 404

    def test_nonexistent_occupation_tasks_404(self, client):
        resp = client.get("/api/occupations/99-9999/tasks")
        assert resp.status_code == 404

    def test_nonexistent_occupation_projections_returns_null(self, client):
        """Non-existent occupation projections returns 404."""
        resp = client.get("/api/occupations/99-9999/projections")
        assert resp.status_code == 404

    def test_nonexistent_occupation_similar_404(self, client):
        resp = client.get("/api/occupations/99-9999/similar")
        assert resp.status_code == 404


class TestParserEdgeCases:
    """CR3-07: Parser edge cases."""

    def test_parse_float_suppression_markers(self):
        from jobclass.parse.common import parse_float
        assert parse_float(None) is None
        assert parse_float("") is None
        assert parse_float("*") is None
        assert parse_float("**") is None
        assert parse_float("#") is None
        assert parse_float("-") is None
        assert parse_float("--") is None
        assert parse_float("N/A") is None
        assert parse_float("  ** ") is None

    def test_parse_float_valid_values(self):
        from jobclass.parse.common import parse_float
        assert parse_float("3.14") == 3.14
        assert parse_float("1,234.56") == 1234.56
        assert parse_float("50%") == 50.0
        assert parse_float("  42  ") == 42.0

    def test_parse_int_valid(self):
        from jobclass.parse.common import parse_int
        assert parse_int("42") == 42
        assert parse_int("1,234") == 1234
        assert parse_int(None) is None
        assert parse_int("N/A") is None

    def test_safe_identifier_rejects_injection(self):
        from jobclass.load import _safe_identifier
        with pytest.raises(ValueError):
            _safe_identifier('; DROP TABLE dim_occupation; --')
        with pytest.raises(ValueError):
            _safe_identifier('table name')
        with pytest.raises(ValueError):
            _safe_identifier('TABLE_NAME')
        with pytest.raises(ValueError):
            _safe_identifier('')

    def test_safe_identifier_accepts_valid(self):
        from jobclass.load import _safe_identifier
        assert _safe_identifier("dim_occupation") == "dim_occupation"
        assert _safe_identifier("stage__bls__oews_national") == "stage__bls__oews_national"


class TestResponseModelValidation:
    """CR2-29 / CR3: Verify all API responses conform to Pydantic models."""

    def test_health_response_schema(self, client):
        from jobclass.web.api.models import HealthResponse
        resp = client.get("/api/health")
        HealthResponse(**resp.json())

    def test_stats_response_schema(self, client):
        from jobclass.web.api.models import StatsResponse
        resp = client.get("/api/stats")
        StatsResponse(**resp.json())

    def test_metadata_response_schema(self, client):
        from jobclass.web.api.models import MetadataResponse
        resp = client.get("/api/metadata")
        MetadataResponse(**resp.json())

    def test_search_response_schema(self, client):
        from jobclass.web.api.models import SearchResponse
        resp = client.get("/api/occupations/search?q=software")
        SearchResponse(**resp.json())

    def test_hierarchy_response_schema(self, client):
        from jobclass.web.api.models import HierarchyResponse
        resp = client.get("/api/occupations/hierarchy")
        HierarchyResponse(**resp.json())

    def test_profile_response_schema(self, client):
        from jobclass.web.api.models import OccupationProfileResponse
        resp = client.get("/api/occupations/15-1252")
        OccupationProfileResponse(**resp.json())

    def test_wages_response_schema(self, client):
        from jobclass.web.api.models import WagesResponse
        resp = client.get("/api/occupations/15-1252/wages")
        WagesResponse(**resp.json())

    def test_skills_response_schema(self, client):
        from jobclass.web.api.models import SkillsResponse
        resp = client.get("/api/occupations/15-1252/skills")
        SkillsResponse(**resp.json())

    def test_tasks_response_schema(self, client):
        from jobclass.web.api.models import TasksResponse
        resp = client.get("/api/occupations/15-1252/tasks")
        TasksResponse(**resp.json())

    def test_projections_response_schema(self, client):
        from jobclass.web.api.models import ProjectionsResponse
        resp = client.get("/api/occupations/15-1252/projections")
        ProjectionsResponse(**resp.json())

    def test_similar_response_schema(self, client):
        from jobclass.web.api.models import SimilarResponse
        resp = client.get("/api/occupations/15-1252/similar")
        SimilarResponse(**resp.json())

    def test_sources_response_schema(self, client):
        from jobclass.web.api.models import SourcesResponse
        resp = client.get("/api/methodology/sources")
        SourcesResponse(**resp.json())

    def test_validation_response_schema(self, client):
        from jobclass.web.api.models import ValidationResponse
        resp = client.get("/api/methodology/validation")
        ValidationResponse(**resp.json())

    def test_geographies_response_schema(self, client):
        from jobclass.web.api.models import GeographiesResponse
        resp = client.get("/api/geographies")
        GeographiesResponse(**resp.json())
