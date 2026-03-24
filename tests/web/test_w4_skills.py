"""Phase W4 tests: Skills, tasks, and similarity endpoints."""


class TestSkillsAPI:
    """WT4-01: Skills endpoint tests."""

    def test_skills_returns_data(self, client):
        resp = client.get("/api/occupations/15-1252/skills")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["skills"]) > 0

    def test_skills_have_names_and_scores(self, client):
        data = client.get("/api/occupations/15-1252/skills").json()
        for s in data["skills"]:
            assert "element_name" in s
            assert "importance" in s
            assert "level" in s

    def test_skills_scores_valid_range(self, client):
        data = client.get("/api/occupations/15-1252/skills").json()
        for s in data["skills"]:
            if s["importance"] is not None:
                assert 0 <= s["importance"] <= 5
            if s["level"] is not None:
                assert 0 <= s["level"] <= 7

    def test_skills_source_version(self, client):
        data = client.get("/api/occupations/15-1252/skills").json()
        assert data["source_version"] is not None

    def test_skills_nonexistent_404(self, client):
        resp = client.get("/api/occupations/99-9999/skills")
        assert resp.status_code == 404


class TestTasksAPI:
    """WT4-02: Tasks endpoint tests."""

    def test_tasks_returns_data(self, client):
        resp = client.get("/api/occupations/15-1252/tasks")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["tasks"]) > 0

    def test_tasks_have_descriptions(self, client):
        data = client.get("/api/occupations/15-1252/tasks").json()
        for t in data["tasks"]:
            assert "task_description" in t
            assert len(t["task_description"]) > 0

    def test_tasks_have_scores(self, client):
        data = client.get("/api/occupations/15-1252/tasks").json()
        for t in data["tasks"]:
            assert "relevance_score" in t

    def test_tasks_source_version(self, client):
        data = client.get("/api/occupations/15-1252/tasks").json()
        assert data["source_version"] is not None


class TestSimilarityAPI:
    """WT4-03: Similar occupations endpoint tests."""

    def test_similar_returns_data(self, client):
        resp = client.get("/api/occupations/15-1252/similar")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["similar"]) > 0

    def test_similar_scores_valid(self, client):
        data = client.get("/api/occupations/15-1252/similar").json()
        for s in data["similar"]:
            assert 0 < s["similarity_score"] <= 1

    def test_similar_has_occupation_info(self, client):
        data = client.get("/api/occupations/15-1252/similar").json()
        for s in data["similar"]:
            assert "soc_code" in s
            assert "occupation_title" in s
            assert s["soc_code"] != "15-1252"  # Should not include self

    def test_similar_nonexistent_404(self, client):
        resp = client.get("/api/occupations/99-9999/similar")
        assert resp.status_code == 404
