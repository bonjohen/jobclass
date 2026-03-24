"""Tests for time-series trend pages and API endpoints (Phase TS9)."""

from __future__ import annotations


class TestTrendPages:
    """Test that all trend pages render successfully."""

    def test_trends_landing(self, client):
        r = client.get("/trends")
        assert r.status_code == 200
        assert "Trends" in r.text

    def test_trend_explorer(self, client):
        r = client.get("/trends/explorer/15-1252")
        assert r.status_code == 200
        assert "Trend Explorer" in r.text

    def test_occupation_comparison(self, client):
        r = client.get("/trends/compare")
        assert r.status_code == 200
        assert "Compare Occupations" in r.text

    def test_geography_comparison(self, client):
        r = client.get("/trends/geography/15-1252")
        assert r.status_code == 200
        assert "Geography Comparison" in r.text

    def test_ranked_movers(self, client):
        r = client.get("/trends/movers")
        assert r.status_code == 200
        assert "Ranked Movers" in r.text


class TestTrendNav:
    """Test that Trends link appears in navigation."""

    def test_trends_in_nav(self, client):
        r = client.get("/")
        assert r.status_code == 200
        assert 'href="/trends"' in r.text


class TestTrendAPI:
    """Test time-series API endpoints."""

    def test_trend_data(self, client):
        r = client.get("/api/trends/15-1252?metric=employment_count")
        assert r.status_code == 200
        data = r.json()
        assert "series" in data
        assert data["soc_code"] == "15-1252"

    def test_trend_data_invalid_soc(self, client):
        r = client.get("/api/trends/invalid")
        assert r.status_code == 400

    def test_compare_occupations(self, client):
        r = client.get("/api/trends/compare/occupations?soc_codes=15-1252,11-1021")
        assert r.status_code == 200
        data = r.json()
        assert "occupations" in data

    def test_compare_geography(self, client):
        r = client.get("/api/trends/compare/geography?soc_code=15-1252")
        assert r.status_code == 200
        data = r.json()
        assert "geographies" in data

    def test_movers(self, client):
        r = client.get("/api/trends/movers?metric=employment_count")
        assert r.status_code == 200
        data = r.json()
        assert "gainers" in data
        assert "losers" in data

    def test_list_metrics(self, client):
        r = client.get("/api/trends/metrics")
        assert r.status_code == 200
        data = r.json()
        assert "metrics" in data
        assert len(data["metrics"]) > 0
        names = {m["metric_name"] for m in data["metrics"]}
        assert "employment_count" in names


class TestMethodologyTimeSeries:
    """TS9-09: Methodology page includes time-series explanation."""

    def test_methodology_has_ts_section(self, client):
        r = client.get("/methodology")
        assert r.status_code == 200
        assert "Comparability Mode" in r.text
        assert "Derived Metrics" in r.text or "Derived" in r.text
        assert "Projected Values" in r.text
