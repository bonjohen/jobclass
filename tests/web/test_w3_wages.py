"""Phase W3 tests: Employment and wages API and display."""


class TestWagesAPI:
    """WT3-01 through WT3-05: Wages endpoint tests."""

    def test_wages_national_returns_data(self, client):
        resp = client.get("/api/occupations/15-1252/wages?geo_type=national")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["wages"]) > 0

    def test_wages_has_employment(self, client):
        data = client.get("/api/occupations/15-1252/wages?geo_type=national").json()
        w = data["wages"][0]
        assert w["employment_count"] is not None

    def test_wages_has_mean_annual(self, client):
        data = client.get("/api/occupations/15-1252/wages?geo_type=national").json()
        w = data["wages"][0]
        assert w["mean_annual_wage"] is not None

    def test_wages_has_median_annual(self, client):
        data = client.get("/api/occupations/15-1252/wages?geo_type=national").json()
        w = data["wages"][0]
        assert w["median_annual_wage"] is not None

    def test_wages_state_returns_multiple(self, client):
        resp = client.get("/api/occupations/15-1252/wages?geo_type=state")
        data = resp.json()
        assert len(data["wages"]) > 0
        # Each entry should have a geo_name
        for w in data["wages"]:
            assert w["geo_name"] is not None or w["geo_code"] is not None

    def test_wages_schema(self, client):
        data = client.get("/api/occupations/15-1252/wages?geo_type=national").json()
        w = data["wages"][0]
        required = [
            "employment_count",
            "mean_annual_wage",
            "median_annual_wage",
            "p10_hourly_wage",
            "p25_hourly_wage",
            "p75_hourly_wage",
            "p90_hourly_wage",
            "source_release_id",
        ]
        for f in required:
            assert f in w

    def test_wages_suppressed_as_null(self, client):
        """Suppressed values must be null, never zero."""
        data = client.get("/api/occupations/15-1252/wages?geo_type=national").json()
        w = data["wages"][0]
        # If a wage field IS null, that's correct (suppressed). If not null, must be positive.
        for field in ["mean_annual_wage", "median_annual_wage"]:
            val = w[field]
            if val is not None:
                assert val > 0, f"{field} should be positive or null, got {val}"

    def test_wages_nonexistent_occupation_404(self, client):
        resp = client.get("/api/occupations/99-9999/wages")
        assert resp.status_code == 404


class TestGeographiesAPI:
    """WT3-03: Geographies endpoint."""

    def test_geographies_returns_list(self, client):
        resp = client.get("/api/geographies")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["geographies"]) > 0

    def test_geographies_have_metadata(self, client):
        data = client.get("/api/geographies").json()
        for g in data["geographies"]:
            assert "geo_type" in g
            assert "geo_code" in g
            assert "geo_name" in g


class TestWagesDisplay:
    """WT3-06 through WT3-10: Wages display and rendering tests."""

    def test_occupation_page_has_wages_section(self, client):
        resp = client.get("/occupation/15-1252")
        assert resp.status_code == 200
        assert "wages-section" in resp.text

    def test_wages_comparison_page_renders(self, client):
        resp = client.get("/occupation/15-1252/wages")
        assert resp.status_code == 200
        assert "wages-table-container" in resp.text

    def test_wages_section_has_lineage(self, client):
        """Wages content div exists for lineage display."""
        resp = client.get("/occupation/15-1252")
        assert "wages-content" in resp.text
