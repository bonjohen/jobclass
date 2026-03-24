"""NDS1/NDS2 tests: Knowledge and Abilities endpoints."""


class TestKnowledgeAPI:
    """NDS1: Knowledge endpoint tests."""

    def test_knowledge_returns_200(self, client):
        resp = client.get("/api/occupations/15-1252/knowledge")
        assert resp.status_code == 200

    def test_knowledge_has_expected_fields(self, client):
        data = client.get("/api/occupations/15-1252/knowledge").json()
        assert "soc_code" in data
        assert "knowledge" in data
        assert "source_version" in data

    def test_knowledge_entries_have_scores(self, client):
        data = client.get("/api/occupations/15-1252/knowledge").json()
        if data["knowledge"]:
            for k in data["knowledge"]:
                assert "element_name" in k
                assert "element_id" in k
                assert "importance" in k
                assert "level" in k

    def test_knowledge_scores_valid_range(self, client):
        data = client.get("/api/occupations/15-1252/knowledge").json()
        for k in data["knowledge"]:
            if k["importance"] is not None:
                assert 0 <= k["importance"] <= 5
            if k["level"] is not None:
                assert 0 <= k["level"] <= 7

    def test_knowledge_nonexistent_404(self, client):
        resp = client.get("/api/occupations/99-9999/knowledge")
        assert resp.status_code == 404

    def test_knowledge_invalid_soc_400(self, client):
        resp = client.get("/api/occupations/INVALID/knowledge")
        assert resp.status_code == 400


class TestAbilitiesAPI:
    """NDS2: Abilities endpoint tests."""

    def test_abilities_returns_200(self, client):
        resp = client.get("/api/occupations/15-1252/abilities")
        assert resp.status_code == 200

    def test_abilities_has_expected_fields(self, client):
        data = client.get("/api/occupations/15-1252/abilities").json()
        assert "soc_code" in data
        assert "abilities" in data
        assert "source_version" in data

    def test_abilities_entries_have_scores(self, client):
        data = client.get("/api/occupations/15-1252/abilities").json()
        if data["abilities"]:
            for a in data["abilities"]:
                assert "element_name" in a
                assert "element_id" in a
                assert "importance" in a
                assert "level" in a

    def test_abilities_scores_valid_range(self, client):
        data = client.get("/api/occupations/15-1252/abilities").json()
        for a in data["abilities"]:
            if a["importance"] is not None:
                assert 0 <= a["importance"] <= 5
            if a["level"] is not None:
                assert 0 <= a["level"] <= 7

    def test_abilities_nonexistent_404(self, client):
        resp = client.get("/api/occupations/99-9999/abilities")
        assert resp.status_code == 404

    def test_abilities_invalid_soc_400(self, client):
        resp = client.get("/api/occupations/INVALID/abilities")
        assert resp.status_code == 400


class TestOccupationProfileSections:
    """Verify occupation page has knowledge and abilities sections."""

    def test_occupation_page_has_knowledge_section(self, client):
        resp = client.get("/occupation/15-1252")
        assert resp.status_code == 200
        assert "knowledge-section" in resp.text
        assert "knowledge-content" in resp.text

    def test_occupation_page_has_abilities_section(self, client):
        resp = client.get("/occupation/15-1252")
        assert resp.status_code == 200
        assert "abilities-section" in resp.text
        assert "abilities-content" in resp.text
