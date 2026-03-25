"""NDS8 / CR2-11a, CR2-12a, CR2-14a: Extended trends test coverage."""

from jobclass.web.api.models import (
    MetricsListResponse,
    TrendCompareResponse,
    TrendGeographyResponse,
    TrendMoversResponse,
    TrendSeriesResponse,
)

# ============================================================
# CR2-11a: Ranked movers year filter
# ============================================================


class TestRankedMoversYearFilter:
    def test_movers_default_year(self, client):
        r = client.get("/api/trends/movers")
        assert r.status_code == 200
        data = r.json()
        assert "year" in data
        assert "available_years" in data

    def test_movers_explicit_year(self, client):
        # Get available years first
        r = client.get("/api/trends/movers")
        data = r.json()
        if data["available_years"]:
            yr = data["available_years"][0]
            r2 = client.get(f"/api/trends/movers?year={yr}")
            assert r2.status_code == 200
            d2 = r2.json()
            assert d2["year"] == yr

    def test_movers_available_years_populated(self, client):
        r = client.get("/api/trends/movers")
        data = r.json()
        assert isinstance(data["available_years"], list)

    def test_movers_nonexistent_year(self, client):
        r = client.get("/api/trends/movers?year=1900")
        assert r.status_code == 200
        data = r.json()
        assert data["gainers"] == []
        assert data["losers"] == []

    def test_movers_year_plus_metric(self, client):
        r = client.get("/api/trends/movers?metric=mean_annual_wage")
        assert r.status_code == 200
        data = r.json()
        assert data["metric"] == "mean_annual_wage"

    def test_movers_gainers_losers_structure(self, client):
        r = client.get("/api/trends/movers")
        data = r.json()
        for mover in data.get("gainers", []):
            assert "soc_code" in mover
            assert "title" in mover
            assert "pct_change" in mover

    def test_movers_custom_limit(self, client):
        r = client.get("/api/trends/movers?limit=5")
        assert r.status_code == 200
        data = r.json()
        assert len(data.get("gainers", [])) <= 5
        assert len(data.get("losers", [])) <= 5


# ============================================================
# CR2-12a: Trends comparison endpoint edge cases
# ============================================================


class TestComparisonEdgeCases:
    def test_compare_too_many_codes(self, client):
        codes = ",".join([f"{i:02d}-0000" for i in range(11)])
        r = client.get(f"/api/trends/compare/occupations?soc_codes={codes}")
        assert r.status_code == 400

    def test_compare_empty_codes(self, client):
        r = client.get("/api/trends/compare/occupations?soc_codes=")
        assert r.status_code == 400

    def test_compare_invalid_soc_format(self, client):
        r = client.get("/api/trends/compare/occupations?soc_codes=INVALID")
        assert r.status_code == 200
        data = r.json()
        # Invalid codes are silently skipped
        assert data["occupations"] == []

    def test_compare_geography_year_param(self, client):
        r = client.get("/api/trends/compare/geography?soc_code=15-1252&year=2024")
        assert r.status_code == 200

    def test_compare_geography_metric_param(self, client):
        r = client.get("/api/trends/compare/geography?soc_code=15-1252&metric=mean_annual_wage")
        assert r.status_code == 200
        data = r.json()
        assert data["metric"] == "mean_annual_wage"

    def test_compare_geography_invalid_soc(self, client):
        r = client.get("/api/trends/compare/geography?soc_code=INVALID")
        assert r.status_code == 400

    def test_compare_geography_missing_data(self, client):
        r = client.get("/api/trends/compare/geography?soc_code=99-9999")
        assert r.status_code == 200
        data = r.json()
        assert data["geographies"] == []

    def test_trend_data_nonexistent_occupation(self, client):
        r = client.get("/api/trends/99-9999")
        assert r.status_code == 200
        data = r.json()
        assert data["series"] == []


# ============================================================
# CR2-14a: Contract tests — Pydantic model validation
# ============================================================


class TestPydanticContracts:
    def test_trend_series_contract(self, client):
        r = client.get("/api/trends/15-1252")
        assert r.status_code == 200
        TrendSeriesResponse.model_validate(r.json())

    def test_trend_series_wage_contract(self, client):
        r = client.get("/api/trends/15-1252?metric=mean_annual_wage")
        assert r.status_code == 200
        TrendSeriesResponse.model_validate(r.json())

    def test_compare_occupations_contract(self, client):
        r = client.get("/api/trends/compare/occupations?soc_codes=15-1252,11-1021")
        assert r.status_code == 200
        TrendCompareResponse.model_validate(r.json())

    def test_compare_geography_contract(self, client):
        r = client.get("/api/trends/compare/geography?soc_code=15-1252")
        assert r.status_code == 200
        TrendGeographyResponse.model_validate(r.json())

    def test_movers_contract(self, client):
        r = client.get("/api/trends/movers")
        assert r.status_code == 200
        TrendMoversResponse.model_validate(r.json())

    def test_metrics_list_contract(self, client):
        r = client.get("/api/trends/metrics")
        assert r.status_code == 200
        MetricsListResponse.model_validate(r.json())

    def test_metrics_include_real_wages(self, client):
        r = client.get("/api/trends/metrics")
        data = r.json()
        names = {m["metric_name"] for m in data["metrics"]}
        assert "real_mean_annual_wage" in names
        assert "real_median_annual_wage" in names


# ============================================================
# Trend explorer template has real wage options
# ============================================================


class TestRealWageUI:
    def test_trend_explorer_has_real_wage_options(self, client):
        r = client.get("/trends/explorer/15-1252")
        assert r.status_code == 200
        assert "real_mean_annual_wage" in r.text
        assert "real_median_annual_wage" in r.text

    def test_ranked_movers_has_real_wage_options(self, client):
        r = client.get("/trends/movers")
        assert r.status_code == 200
        assert "real_mean_annual_wage" in r.text
        assert "real_median_annual_wage" in r.text
