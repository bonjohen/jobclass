"""Phase W9 tests: End-to-end integration, worked example, deployment readiness."""



class TestWorkedExample:
    """WT9-01, WT9-02: Software Developers (15-1252) complete worked example."""

    def test_profile_api_complete(self, client):
        """Full profile data available for 15-1252."""
        data = client.get("/api/occupations/15-1252").json()
        assert data["soc_code"] == "15-1252"
        assert data["occupation_title"] is not None
        assert data["occupation_definition"] is not None
        assert data["soc_version"] == "2018"
        assert len(data["breadcrumb"]) > 0

    def test_wages_available(self, client):
        data = client.get("/api/occupations/15-1252/wages?geo_type=national").json()
        assert len(data["wages"]) > 0
        w = data["wages"][0]
        assert w["employment_count"] is not None
        assert w["mean_annual_wage"] is not None

    def test_state_wages_available(self, client):
        data = client.get("/api/occupations/15-1252/wages?geo_type=state").json()
        assert len(data["wages"]) > 0

    def test_skills_available(self, client):
        data = client.get("/api/occupations/15-1252/skills").json()
        assert len(data["skills"]) > 0
        assert data["source_version"] is not None

    def test_tasks_available(self, client):
        data = client.get("/api/occupations/15-1252/tasks").json()
        assert len(data["tasks"]) > 0

    def test_projections_available(self, client):
        data = client.get("/api/occupations/15-1252/projections").json()
        assert data["projections"] is not None
        p = data["projections"]
        assert p["base_employment"] is not None
        assert p["projected_employment"] is not None

    def test_similar_available(self, client):
        data = client.get("/api/occupations/15-1252/similar").json()
        assert len(data["similar"]) > 0

    def test_profile_page_renders(self, client):
        resp = client.get("/occupation/15-1252")
        assert resp.status_code == 200
        assert 'data-soc-code="15-1252"' in resp.text


class TestSourceLineage:
    """WT9-03: Every data section exposes source lineage."""

    def test_wages_have_source(self, client):
        data = client.get("/api/occupations/15-1252/wages?geo_type=national").json()
        assert data["wages"][0]["source_release_id"] is not None

    def test_skills_have_source(self, client):
        data = client.get("/api/occupations/15-1252/skills").json()
        assert data["source_version"] is not None

    def test_tasks_have_source(self, client):
        data = client.get("/api/occupations/15-1252/tasks").json()
        assert data["source_version"] is not None

    def test_projections_have_source(self, client):
        data = client.get("/api/occupations/15-1252/projections").json()
        assert data["projections"]["source_release_id"] is not None

    def test_profile_has_source(self, client):
        data = client.get("/api/occupations/15-1252").json()
        assert data["source_release_id"] is not None


class TestMethodologyComplete:
    """WT9-04: Methodology pages complete and accurate."""

    def test_sources_complete(self, client):
        data = client.get("/api/methodology/sources").json()
        assert len(data["sources"]) == 4
        for s in data["sources"]:
            assert s["current_version"] is not None

    def test_validation_passes(self, client):
        data = client.get("/api/methodology/validation").json()
        assert data["all_passed"] is True


class TestSmokeTests:
    """WT9-05 through WT9-08: Full application smoke tests."""

    def test_landing_to_search_flow(self, client):
        """Landing page loads, links to search which works."""
        resp = client.get("/")
        assert resp.status_code == 200
        assert 'href="/search"' in resp.text
        resp = client.get("/search")
        assert resp.status_code == 200

    def test_search_to_profile_flow(self, client):
        """Search returns results, profile page loads."""
        data = client.get("/api/occupations/search?q=Software").json()
        assert len(data["results"]) > 0
        code = data["results"][0]["soc_code"]
        resp = client.get(f"/occupation/{code}")
        assert resp.status_code == 200

    def test_hierarchy_navigable(self, client):
        data = client.get("/api/occupations/hierarchy").json()
        assert len(data["hierarchy"]) > 0
        resp = client.get("/hierarchy")
        assert resp.status_code == 200

    def test_all_api_endpoints_respond(self, client):
        """Verify all API endpoints return non-error responses."""
        endpoints = [
            "/api/health",
            "/api/metadata",
            "/api/stats",
            "/api/occupations/search?q=test",
            "/api/occupations/hierarchy",
            "/api/occupations/15-1252",
            "/api/occupations/15-1252/wages",
            "/api/occupations/15-1252/skills",
            "/api/occupations/15-1252/tasks",
            "/api/occupations/15-1252/projections",
            "/api/occupations/15-1252/similar",
            "/api/geographies",
            "/api/methodology/sources",
            "/api/methodology/validation",
        ]
        for ep in endpoints:
            resp = client.get(ep)
            assert resp.status_code == 200, f"Endpoint {ep} returned {resp.status_code}"

    def test_all_pages_render(self, client):
        """Verify all page routes return 200."""
        pages = [
            "/",
            "/search",
            "/hierarchy",
            "/methodology",
            "/occupation/15-1252",
            "/occupation/15-1252/wages",
        ]
        for page in pages:
            resp = client.get(page)
            assert resp.status_code == 200, f"Page {page} returned {resp.status_code}"
