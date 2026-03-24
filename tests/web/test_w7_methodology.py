"""Phase W7 tests: Methodology, sources, and validation endpoints."""


class TestSourcesAPI:
    """WT7-01: Methodology sources endpoint."""

    def test_sources_returns_data(self, client):
        resp = client.get("/api/methodology/sources")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["sources"]) == 4

    def test_sources_have_names(self, client):
        data = client.get("/api/methodology/sources").json()
        names = [s["name"] for s in data["sources"]]
        assert any("SOC" in n for n in names)
        assert any("OEWS" in n for n in names)
        assert any("O*NET" in n for n in names)
        assert any("Projections" in n for n in names)

    def test_sources_have_versions(self, client):
        data = client.get("/api/methodology/sources").json()
        for s in data["sources"]:
            assert "current_version" in s
            assert "url" in s
            assert "refresh_cadence" in s

    def test_sources_soc_version_populated(self, client):
        data = client.get("/api/methodology/sources").json()
        soc = [s for s in data["sources"] if "SOC" in s["name"]][0]
        assert soc["current_version"] is not None


class TestValidationAPI:
    """WT7-02: Validation summary endpoint."""

    def test_validation_returns_summary(self, client):
        resp = client.get("/api/methodology/validation")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_checks" in data
        assert "passed" in data
        assert "checks" in data

    def test_validation_all_passed(self, client):
        data = client.get("/api/methodology/validation").json()
        assert data["all_passed"] is True

    def test_validation_checks_populated(self, client):
        data = client.get("/api/methodology/validation").json()
        assert data["total_checks"] >= 5
        for c in data["checks"]:
            assert "check" in c
            assert "passed" in c
            assert "detail" in c

    def test_validation_marts_checked(self, client):
        data = client.get("/api/methodology/validation").json()
        check_names = [c["check"] for c in data["checks"]]
        assert any("occupation_summary" in n for n in check_names)
        assert any("occupation_skill_profile" in n for n in check_names)


class TestMethodologyPage:
    """WT7-03 through WT7-05: Methodology page rendering."""

    def test_methodology_page_renders(self, client):
        resp = client.get("/methodology")
        assert resp.status_code == 200

    def test_methodology_has_architecture(self, client):
        html = client.get("/methodology").text
        assert "Architecture" in html
        assert "Raw/Landing" in html

    def test_methodology_has_data_sources(self, client):
        html = client.get("/methodology").text
        assert "Data Sources" in html
        assert "Bureau of Labor Statistics" in html

    def test_methodology_has_quality(self, client):
        html = client.get("/methodology").text
        assert "Data Quality" in html
        assert "Idempotent" in html

    def test_methodology_has_versions(self, client):
        html = client.get("/methodology").text
        assert "versions-content" in html

    def test_methodology_has_validation(self, client):
        html = client.get("/methodology").text
        assert "validation-content" in html
