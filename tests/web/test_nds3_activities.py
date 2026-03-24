"""NDS3 tests: Work Activities endpoint."""


class TestActivitiesAPI:
    """NDS3: Work Activities endpoint tests."""

    def test_activities_returns_200(self, client):
        resp = client.get("/api/occupations/15-1252/activities")
        assert resp.status_code == 200

    def test_activities_has_expected_fields(self, client):
        data = client.get("/api/occupations/15-1252/activities").json()
        assert "soc_code" in data
        assert "activities" in data
        assert "source_version" in data

    def test_activities_entries_have_scores(self, client):
        data = client.get("/api/occupations/15-1252/activities").json()
        if data["activities"]:
            for a in data["activities"]:
                assert "element_name" in a
                assert "element_id" in a
                assert "importance" in a
                assert "level" in a

    def test_activities_scores_valid_range(self, client):
        data = client.get("/api/occupations/15-1252/activities").json()
        for a in data["activities"]:
            if a["importance"] is not None:
                assert 0 <= a["importance"] <= 5
            if a["level"] is not None:
                assert 0 <= a["level"] <= 7

    def test_activities_returns_data(self, client):
        data = client.get("/api/occupations/15-1252/activities").json()
        assert len(data["activities"]) > 0

    def test_activities_nonexistent_404(self, client):
        resp = client.get("/api/occupations/99-9999/activities")
        assert resp.status_code == 404

    def test_activities_invalid_soc_400(self, client):
        resp = client.get("/api/occupations/INVALID/activities")
        assert resp.status_code == 400


class TestOccupationProfileActivitiesSection:
    """Verify occupation page has work activities section."""

    def test_occupation_page_has_activities_section(self, client):
        resp = client.get("/occupation/15-1252")
        assert resp.status_code == 200
        assert "activities-section" in resp.text
        assert "activities-content" in resp.text
