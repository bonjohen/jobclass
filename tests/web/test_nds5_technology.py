"""NDS5 tests: Technology Skills endpoint."""


class TestTechnologyAPI:
    """NDS5: Technology Skills endpoint tests."""

    def test_technology_returns_200(self, client):
        resp = client.get("/api/occupations/15-1252/technology")
        assert resp.status_code == 200

    def test_technology_has_expected_fields(self, client):
        data = client.get("/api/occupations/15-1252/technology").json()
        assert "soc_code" in data
        assert "groups" in data
        assert "source_version" in data

    def test_technology_returns_data(self, client):
        data = client.get("/api/occupations/15-1252/technology").json()
        assert len(data["groups"]) > 0

    def test_technology_groups_have_items(self, client):
        data = client.get("/api/occupations/15-1252/technology").json()
        for group in data["groups"]:
            assert "t2_type" in group
            assert "items" in group
            assert len(group["items"]) > 0

    def test_technology_items_have_fields(self, client):
        data = client.get("/api/occupations/15-1252/technology").json()
        for group in data["groups"]:
            for item in group["items"]:
                assert "example_name" in item
                assert "hot_technology" in item

    def test_technology_has_tools_and_tech(self, client):
        data = client.get("/api/occupations/15-1252/technology").json()
        types = {g["t2_type"] for g in data["groups"]}
        assert "Tools" in types
        assert "Technology" in types

    def test_technology_nonexistent_404(self, client):
        resp = client.get("/api/occupations/99-9999/technology")
        assert resp.status_code == 404

    def test_technology_invalid_soc_400(self, client):
        resp = client.get("/api/occupations/INVALID/technology")
        assert resp.status_code == 400


class TestOccupationProfileTechnologySection:
    """Verify occupation page has technology section."""

    def test_occupation_page_has_technology_section(self, client):
        resp = client.get("/occupation/15-1252")
        assert resp.status_code == 200
        assert "technology-section" in resp.text
        assert "technology-content" in resp.text
