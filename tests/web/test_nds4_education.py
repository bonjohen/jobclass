"""NDS4 tests: Education & Training endpoint."""


class TestEducationAPI:
    """NDS4: Education endpoint tests."""

    def test_education_returns_200(self, client):
        resp = client.get("/api/occupations/15-1252/education")
        assert resp.status_code == 200

    def test_education_has_expected_fields(self, client):
        data = client.get("/api/occupations/15-1252/education").json()
        assert "soc_code" in data
        assert "elements" in data
        assert "source_version" in data
        assert "summary" in data

    def test_education_returns_data(self, client):
        data = client.get("/api/occupations/15-1252/education").json()
        assert len(data["elements"]) > 0

    def test_education_elements_have_categories(self, client):
        data = client.get("/api/occupations/15-1252/education").json()
        for elem in data["elements"]:
            assert "element_id" in elem
            assert "element_name" in elem
            assert "scale_id" in elem
            assert "categories" in elem
            assert len(elem["categories"]) > 0

    def test_education_categories_have_percentage(self, client):
        data = client.get("/api/occupations/15-1252/education").json()
        for elem in data["elements"]:
            for cat in elem["categories"]:
                assert "category" in cat
                assert "percentage" in cat

    def test_education_summary_present(self, client):
        data = client.get("/api/occupations/15-1252/education").json()
        # With our fixture data, 15-1252 has RL category 5 at 55%
        assert data["summary"] is not None
        assert "Typical:" in data["summary"]

    def test_education_nonexistent_404(self, client):
        resp = client.get("/api/occupations/99-9999/education")
        assert resp.status_code == 404

    def test_education_invalid_soc_400(self, client):
        resp = client.get("/api/occupations/INVALID/education")
        assert resp.status_code == 400


class TestOccupationProfileEducationSection:
    """Verify occupation page has education section."""

    def test_occupation_page_has_education_section(self, client):
        resp = client.get("/occupation/15-1252")
        assert resp.status_code == 200
        assert "education-section" in resp.text
        assert "education-content" in resp.text
