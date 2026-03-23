"""T4-01 through T4-05: OEWS parser unit tests."""

from jobclass.parse.oews import parse_oews


class TestOewsNationalParser:
    """T4-01: OEWS national parser extracts expected fields."""

    def test_extracts_known_occupations(self, oews_national_content):
        rows = parse_oews(oews_national_content, "2024.05")
        codes = {r.occupation_code for r in rows}
        assert "15-1252" in codes
        assert "11-1021" in codes

    def test_wage_fields_numeric(self, oews_national_content):
        rows = parse_oews(oews_national_content, "2024.05")
        sw = [r for r in rows if r.occupation_code == "15-1252"][0]
        assert isinstance(sw.mean_annual_wage, float)
        assert sw.mean_annual_wage == 130490.0

    def test_employment_is_int(self, oews_national_content):
        rows = parse_oews(oews_national_content, "2024.05")
        sw = [r for r in rows if r.occupation_code == "15-1252"][0]
        assert isinstance(sw.employment_count, int)
        assert sw.employment_count == 1795300


class TestOewsStateParser:
    """T4-02: OEWS state parser same schema as national."""

    def test_same_fields(self, oews_national_content, oews_state_content):
        nat = parse_oews(oews_national_content, "2024.05")
        st = parse_oews(oews_state_content, "2024.05")
        assert set(vars(nat[0]).keys()) == set(vars(st[0]).keys())


class TestOewsSuppression:
    """T4-03: OEWS parsers preserve suppressed values as None."""

    def test_suppressed_as_none(self, oews_national_content):
        rows = parse_oews(oews_national_content, "2024.05")
        ceo = [r for r in rows if r.occupation_code == "11-1011"][0]
        # CEO has ** for several wage fields
        assert ceo.mean_hourly_wage is None
        assert ceo.mean_annual_wage is None


class TestOewsNaming:
    """T4-04: OEWS parsers apply snake_case and explicit types."""

    def test_snake_case(self, oews_national_content):
        rows = parse_oews(oews_national_content, "2024.05")
        r = rows[0]
        assert hasattr(r, "occupation_code")
        assert hasattr(r, "mean_annual_wage")
        assert hasattr(r, "employment_count")

    def test_codes_are_text(self, oews_national_content):
        rows = parse_oews(oews_national_content, "2024.05")
        for r in rows:
            assert isinstance(r.occupation_code, str)
            assert isinstance(r.area_code, str)


class TestOewsMetadata:
    """T4-05: OEWS parsers attach source_release_id and parser_version."""

    def test_metadata_present(self, oews_national_content):
        rows = parse_oews(oews_national_content, "2024.05")
        for r in rows:
            assert r.source_release_id == "2024.05"
            assert r.parser_version
