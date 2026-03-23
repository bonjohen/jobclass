"""T3-01 through T3-04: SOC parser unit tests."""

from jobclass.parse.soc import parse_soc_definitions, parse_soc_hierarchy


class TestSocHierarchyParser:
    """T3-01: SOC hierarchy parser extracts correct fields."""

    def test_extracts_major_group(self, soc_hierarchy_content):
        rows = parse_soc_hierarchy(soc_hierarchy_content, "2018")
        majors = [r for r in rows if r.occupation_level == 1]
        assert len(majors) >= 1
        assert any(r.soc_code == "11-0000" for r in majors)
        assert any(r.soc_code == "15-0000" for r in majors)

    def test_extracts_minor_group(self, soc_hierarchy_content):
        rows = parse_soc_hierarchy(soc_hierarchy_content, "2018")
        minors = [r for r in rows if r.occupation_level == 2]
        assert any(r.soc_code == "11-1000" for r in minors)

    def test_extracts_broad_occupation(self, soc_hierarchy_content):
        rows = parse_soc_hierarchy(soc_hierarchy_content, "2018")
        broads = [r for r in rows if r.occupation_level == 3]
        assert any(r.soc_code == "15-1250" for r in broads)

    def test_extracts_detailed_occupation(self, soc_hierarchy_content):
        rows = parse_soc_hierarchy(soc_hierarchy_content, "2018")
        details = [r for r in rows if r.occupation_level == 4]
        assert any(r.soc_code == "15-1252" for r in details)
        sw_dev = [r for r in details if r.soc_code == "15-1252"][0]
        assert sw_dev.occupation_title == "Software Developers"

    def test_parent_links_correct(self, soc_hierarchy_content):
        rows = parse_soc_hierarchy(soc_hierarchy_content, "2018")
        by_code = {r.soc_code: r for r in rows}
        # Major has no parent
        assert by_code["11-0000"].parent_soc_code is None
        # Minor's parent is major
        assert by_code["11-1000"].parent_soc_code == "11-0000"
        # Broad's parent is minor
        assert by_code["15-1250"].parent_soc_code == "15-1200"
        # Detailed's parent is broad
        assert by_code["15-1252"].parent_soc_code == "15-1250"


class TestSocHierarchyEdgeCases:
    """T3-02: SOC hierarchy parser handles edge cases."""

    def test_all_other_category(self, soc_hierarchy_content):
        rows = parse_soc_hierarchy(soc_hierarchy_content, "2018")
        all_other = [r for r in rows if "All Other" in r.occupation_title]
        assert len(all_other) >= 1
        # "All Other" codes end in 90 (broad) or 99 (detailed)
        for r in all_other:
            suffix = r.soc_code.split("-")[1]
            assert suffix.endswith("90") or suffix.endswith("99"), f"Unexpected All Other code: {r.soc_code}"

    def test_trailing_zeros_preserved(self, soc_hierarchy_content):
        rows = parse_soc_hierarchy(soc_hierarchy_content, "2018")
        major = [r for r in rows if r.soc_code == "11-0000"]
        assert len(major) == 1
        assert major[0].soc_code == "11-0000"  # Not truncated


class TestSocDefinitionsParser:
    """T3-03: SOC definitions parser extracts code and definition text."""

    def test_extracts_definitions(self, soc_definitions_content):
        rows = parse_soc_definitions(soc_definitions_content, "2018")
        assert len(rows) >= 1
        for row in rows:
            assert row.soc_code
            assert row.occupation_definition
            # Code format matches XX-XXXX
            assert len(row.soc_code) == 7
            assert row.soc_code[2] == "-"

    def test_software_developers_definition(self, soc_definitions_content):
        rows = parse_soc_definitions(soc_definitions_content, "2018")
        sw = [r for r in rows if r.soc_code == "15-1252"]
        assert len(sw) == 1
        assert "software" in sw[0].occupation_definition.lower()


class TestSocParserNaming:
    """T3-04: SOC parsers apply snake_case names and explicit types."""

    def test_hierarchy_field_names_snake_case(self, soc_hierarchy_content):
        rows = parse_soc_hierarchy(soc_hierarchy_content, "2018")
        row = rows[0]
        # Check field names via dataclass
        assert hasattr(row, "soc_code")
        assert hasattr(row, "occupation_title")
        assert hasattr(row, "occupation_level")
        assert hasattr(row, "occupation_level_name")
        assert hasattr(row, "parent_soc_code")

    def test_hierarchy_types(self, soc_hierarchy_content):
        rows = parse_soc_hierarchy(soc_hierarchy_content, "2018")
        for row in rows:
            assert isinstance(row.soc_code, str)
            assert isinstance(row.occupation_level, int)
            assert isinstance(row.occupation_title, str)

    def test_definitions_types(self, soc_definitions_content):
        rows = parse_soc_definitions(soc_definitions_content, "2018")
        for row in rows:
            assert isinstance(row.soc_code, str)
            assert isinstance(row.occupation_definition, str)
