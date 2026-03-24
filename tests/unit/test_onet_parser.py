"""T5-01 through T5-06: O*NET parser unit tests."""

from jobclass.parse.onet import parse_onet_descriptors, parse_onet_tasks

RELEASE = "29.1"


class TestOnetSkillsParser:
    """T5-01: O*NET skills parser extracts expected fields."""

    def test_extracts_known_skill_pairs(self, onet_skills_content):
        rows = parse_onet_descriptors(onet_skills_content, RELEASE)
        pairs = {(r.occupation_code, r.element_id, r.scale_id) for r in rows}
        assert ("15-1252", "2.A.1.a", "IM") in pairs
        assert ("15-1252", "2.B.3.a", "LV") in pairs
        assert ("11-1021", "2.A.1.b", "IM") in pairs

    def test_data_value_numeric(self, onet_skills_content):
        rows = parse_onet_descriptors(onet_skills_content, RELEASE)
        sw = [r for r in rows if r.occupation_code == "15-1252" and r.element_id == "2.A.1.a" and r.scale_id == "IM"][0]
        assert isinstance(sw.data_value, float)
        assert sw.data_value == 4.25

    def test_strips_onet_suffix(self, onet_skills_content):
        rows = parse_onet_descriptors(onet_skills_content, RELEASE)
        for r in rows:
            assert "." not in r.occupation_code  # .00 suffix stripped


class TestOnetKnowledgeParser:
    """T5-02: O*NET knowledge parser extracts expected fields."""

    def test_extracts_known_knowledge_pairs(self, onet_knowledge_content):
        rows = parse_onet_descriptors(onet_knowledge_content, RELEASE)
        pairs = {(r.occupation_code, r.element_id) for r in rows}
        assert ("15-1252", "2.C.3.a") in pairs
        assert ("11-1021", "2.C.1.a") in pairs

    def test_element_name_preserved(self, onet_knowledge_content):
        rows = parse_onet_descriptors(onet_knowledge_content, RELEASE)
        ce = [r for r in rows if r.element_id == "2.C.3.a" and r.occupation_code == "15-1252"][0]
        assert ce.element_name == "Computers and Electronics"


class TestOnetAbilitiesParser:
    """T5-03: O*NET abilities parser extracts expected fields."""

    def test_extracts_known_ability_pairs(self, onet_abilities_content):
        rows = parse_onet_descriptors(onet_abilities_content, RELEASE)
        pairs = {(r.occupation_code, r.element_id) for r in rows}
        assert ("15-1252", "1.A.1.b.2") in pairs
        assert ("11-1021", "1.A.1.b.4") in pairs


class TestOnetTasksParser:
    """T5-04: O*NET tasks parser extracts expected fields."""

    def test_extracts_known_tasks(self, onet_tasks_content):
        rows = parse_onet_tasks(onet_tasks_content, RELEASE)
        task_ids = {r.task_id for r in rows}
        assert "19701" in task_ids
        assert "4607" in task_ids
        assert "4601" in task_ids

    def test_task_text_preserved(self, onet_tasks_content):
        rows = parse_onet_tasks(onet_tasks_content, RELEASE)
        t = [r for r in rows if r.task_id == "19701"][0]
        assert "Analyze user needs" in t.task

    def test_incumbents_is_int(self, onet_tasks_content):
        rows = parse_onet_tasks(onet_tasks_content, RELEASE)
        for r in rows:
            if r.incumbents_responding is not None:
                assert isinstance(r.incumbents_responding, int)


class TestOnetNaming:
    """T5-05: All O*NET parsers apply snake_case and explicit types."""

    def test_descriptor_snake_case(self, onet_skills_content):
        rows = parse_onet_descriptors(onet_skills_content, RELEASE)
        r = rows[0]
        assert hasattr(r, "occupation_code")
        assert hasattr(r, "element_id")
        assert hasattr(r, "data_value")
        assert hasattr(r, "scale_id")

    def test_task_snake_case(self, onet_tasks_content):
        rows = parse_onet_tasks(onet_tasks_content, RELEASE)
        r = rows[0]
        assert hasattr(r, "occupation_code")
        assert hasattr(r, "task_id")
        assert hasattr(r, "task_type")

    def test_codes_are_text(self, onet_skills_content):
        rows = parse_onet_descriptors(onet_skills_content, RELEASE)
        for r in rows:
            assert isinstance(r.occupation_code, str)
            assert isinstance(r.element_id, str)


class TestOnetMetadata:
    """T5-06: All O*NET parsers attach source_release_id and parser_version."""

    def test_descriptor_metadata(self, onet_skills_content):
        rows = parse_onet_descriptors(onet_skills_content, RELEASE)
        for r in rows:
            assert r.source_release_id == RELEASE
            assert r.parser_version

    def test_task_metadata(self, onet_tasks_content):
        rows = parse_onet_tasks(onet_tasks_content, RELEASE)
        for r in rows:
            assert r.source_release_id == RELEASE
            assert r.parser_version
