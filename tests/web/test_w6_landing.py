"""Phase W6 tests: Landing page, stats, navigation."""

import pytest


class TestStatsAPI:
    """WT6-01: Stats endpoint tests."""

    def test_stats_returns_200(self, client):
        resp = client.get("/api/stats")
        assert resp.status_code == 200

    def test_stats_has_counts(self, client):
        data = client.get("/api/stats").json()
        assert data["occupation_count"] > 0
        assert data["geography_count"] > 0

    def test_stats_has_skill_count(self, client):
        data = client.get("/api/stats").json()
        assert data["skill_count"] > 0

    def test_stats_has_task_count(self, client):
        data = client.get("/api/stats").json()
        assert data["task_count"] > 0


class TestLandingPage:
    """WT6-02, WT6-03: Landing page rendering."""

    def test_landing_has_stats_section(self, client):
        resp = client.get("/")
        assert "stats-bar" in resp.text

    def test_landing_has_spotlight(self, client):
        resp = client.get("/")
        assert "spotlight" in resp.text

    def test_landing_has_entry_cards(self, client):
        html = client.get("/").text
        assert "Search Occupations" in html
        assert "Browse Hierarchy" in html
        assert "Methodology" in html


class TestNavigation:
    """WT6-04, WT6-05, WT6-06: Navigation and meta."""

    def test_nav_has_all_links(self, client):
        html = client.get("/").text
        assert 'href="/search"' in html or 'href="/search"' in html
        assert 'href="/hierarchy"' in html
        assert 'href="/methodology"' in html

    def test_search_page_reachable(self, client):
        assert client.get("/search").status_code == 200

    def test_hierarchy_page_reachable(self, client):
        assert client.get("/hierarchy").status_code == 200

    def test_methodology_page_reachable(self, client):
        assert client.get("/methodology").status_code == 200

    def test_404_page_has_navigation(self, client):
        resp = client.get("/nonexistent")
        assert resp.status_code == 404
        assert "Return to Home" in resp.text
        assert "Search Occupations" in resp.text

    def test_pages_have_titles(self, client):
        pages = [("/", "JobClass"), ("/search", "Search"), ("/hierarchy", "Hierarchy")]
        for path, expected in pages:
            html = client.get(path).text
            assert "<title>" in html
            assert expected in html

    def test_pages_have_meta_description(self, client):
        html = client.get("/").text
        assert 'name="description"' in html
