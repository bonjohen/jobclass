"""T5-07 through T5-32: O*NET staging, dimensions, bridges, validations, idempotence tests."""

from jobclass.load.onet import (
    load_bridge_occupation_descriptor,
    load_bridge_occupation_task,
    load_dim_descriptor,
    load_dim_task,
)
from jobclass.validate.onet import (
    validate_onet_occupation_mapping,
    validate_onet_soc_alignment,
    validate_onet_structural,
)

RELEASE = "29.1"
SOC_VER = "2018"
ONET_VER = "29.1"


class TestOnetStagingContract:
    """T5-07 through T5-10: Staging tables have required columns."""

    def test_skills_columns(self, onet_loaded_db):
        cols = {
            r[0]
            for r in onet_loaded_db.execute(
                "SELECT column_name FROM information_schema.columns WHERE table_name = 'stage__onet__skills'"
            ).fetchall()
        }
        for c in [
            "occupation_code",
            "element_id",
            "element_name",
            "scale_id",
            "data_value",
            "source_release_id",
            "parser_version",
        ]:
            assert c in cols

    def test_knowledge_columns(self, onet_loaded_db):
        cols = {
            r[0]
            for r in onet_loaded_db.execute(
                "SELECT column_name FROM information_schema.columns WHERE table_name = 'stage__onet__knowledge'"
            ).fetchall()
        }
        for c in ["occupation_code", "element_id", "data_value", "source_release_id"]:
            assert c in cols

    def test_abilities_columns(self, onet_loaded_db):
        cols = {
            r[0]
            for r in onet_loaded_db.execute(
                "SELECT column_name FROM information_schema.columns WHERE table_name = 'stage__onet__abilities'"
            ).fetchall()
        }
        for c in ["occupation_code", "element_id", "data_value", "source_release_id"]:
            assert c in cols

    def test_tasks_columns(self, onet_loaded_db):
        cols = {
            r[0]
            for r in onet_loaded_db.execute(
                "SELECT column_name FROM information_schema.columns WHERE table_name = 'stage__onet__tasks'"
            ).fetchall()
        }
        for c in ["occupation_code", "task_id", "task", "source_release_id", "parser_version"]:
            assert c in cols


class TestOnetStagingGrain:
    """T5-11 through T5-14: Staging grain uniqueness."""

    def test_skills_no_duplicates(self, onet_loaded_db):
        dups = onet_loaded_db.execute(
            """SELECT occupation_code, element_id, scale_id, COUNT(*) FROM stage__onet__skills
               WHERE source_release_id = ?
               GROUP BY occupation_code, element_id, scale_id, source_release_id
               HAVING COUNT(*) > 1""",
            [RELEASE],
        ).fetchall()
        assert len(dups) == 0

    def test_knowledge_no_duplicates(self, onet_loaded_db):
        dups = onet_loaded_db.execute(
            """SELECT occupation_code, element_id, scale_id, COUNT(*) FROM stage__onet__knowledge
               WHERE source_release_id = ?
               GROUP BY occupation_code, element_id, scale_id, source_release_id
               HAVING COUNT(*) > 1""",
            [RELEASE],
        ).fetchall()
        assert len(dups) == 0

    def test_abilities_no_duplicates(self, onet_loaded_db):
        dups = onet_loaded_db.execute(
            """SELECT occupation_code, element_id, scale_id, COUNT(*) FROM stage__onet__abilities
               WHERE source_release_id = ?
               GROUP BY occupation_code, element_id, scale_id, source_release_id
               HAVING COUNT(*) > 1""",
            [RELEASE],
        ).fetchall()
        assert len(dups) == 0

    def test_tasks_no_duplicates(self, onet_loaded_db):
        dups = onet_loaded_db.execute(
            """SELECT occupation_code, task_id, COUNT(*) FROM stage__onet__tasks
               WHERE source_release_id = ?
               GROUP BY occupation_code, task_id, source_release_id
               HAVING COUNT(*) > 1""",
            [RELEASE],
        ).fetchall()
        assert len(dups) == 0


class TestDimDescriptors:
    """T5-15 through T5-19: Descriptor dimension grain and contract."""

    def test_dim_skill_no_duplicates(self, onet_loaded_db):
        dups = onet_loaded_db.execute(
            """SELECT element_id, source_version, COUNT(*) FROM dim_skill
               GROUP BY element_id, source_version HAVING COUNT(*) > 1"""
        ).fetchall()
        assert len(dups) == 0

    def test_dim_knowledge_no_duplicates(self, onet_loaded_db):
        dups = onet_loaded_db.execute(
            """SELECT element_id, source_version, COUNT(*) FROM dim_knowledge
               GROUP BY element_id, source_version HAVING COUNT(*) > 1"""
        ).fetchall()
        assert len(dups) == 0

    def test_dim_ability_no_duplicates(self, onet_loaded_db):
        dups = onet_loaded_db.execute(
            """SELECT element_id, source_version, COUNT(*) FROM dim_ability
               GROUP BY element_id, source_version HAVING COUNT(*) > 1"""
        ).fetchall()
        assert len(dups) == 0

    def test_dim_task_no_duplicates(self, onet_loaded_db):
        dups = onet_loaded_db.execute(
            """SELECT task_id, source_version, COUNT(*) FROM dim_task
               GROUP BY task_id, source_version HAVING COUNT(*) > 1"""
        ).fetchall()
        assert len(dups) == 0

    def test_dim_skill_required_fields(self, onet_loaded_db):
        cols = {
            r[0]
            for r in onet_loaded_db.execute(
                "SELECT column_name FROM information_schema.columns WHERE table_name = 'dim_skill'"
            ).fetchall()
        }
        for c in ["skill_key", "element_id", "element_name", "source_version", "is_current"]:
            assert c in cols

    def test_dim_knowledge_required_fields(self, onet_loaded_db):
        cols = {
            r[0]
            for r in onet_loaded_db.execute(
                "SELECT column_name FROM information_schema.columns WHERE table_name = 'dim_knowledge'"
            ).fetchall()
        }
        for c in ["knowledge_key", "element_id", "element_name", "source_version", "is_current"]:
            assert c in cols

    def test_dim_ability_required_fields(self, onet_loaded_db):
        cols = {
            r[0]
            for r in onet_loaded_db.execute(
                "SELECT column_name FROM information_schema.columns WHERE table_name = 'dim_ability'"
            ).fetchall()
        }
        for c in ["ability_key", "element_id", "element_name", "source_version", "is_current"]:
            assert c in cols

    def test_dim_task_required_fields(self, onet_loaded_db):
        cols = {
            r[0]
            for r in onet_loaded_db.execute(
                "SELECT column_name FROM information_schema.columns WHERE table_name = 'dim_task'"
            ).fetchall()
        }
        for c in ["task_key", "task_id", "task", "source_version", "is_current"]:
            assert c in cols


class TestBridgeTables:
    """T5-20 through T5-28: Bridge grain uniqueness and referential integrity."""

    def test_bridge_skill_no_duplicates(self, onet_loaded_db):
        dups = onet_loaded_db.execute(
            """SELECT occupation_key, skill_key, scale_id, source_version, COUNT(*)
               FROM bridge_occupation_skill
               GROUP BY occupation_key, skill_key, scale_id, source_version
               HAVING COUNT(*) > 1"""
        ).fetchall()
        assert len(dups) == 0

    def test_bridge_knowledge_no_duplicates(self, onet_loaded_db):
        dups = onet_loaded_db.execute(
            """SELECT occupation_key, knowledge_key, scale_id, source_version, COUNT(*)
               FROM bridge_occupation_knowledge
               GROUP BY occupation_key, knowledge_key, scale_id, source_version
               HAVING COUNT(*) > 1"""
        ).fetchall()
        assert len(dups) == 0

    def test_bridge_ability_no_duplicates(self, onet_loaded_db):
        dups = onet_loaded_db.execute(
            """SELECT occupation_key, ability_key, scale_id, source_version, COUNT(*)
               FROM bridge_occupation_ability
               GROUP BY occupation_key, ability_key, scale_id, source_version
               HAVING COUNT(*) > 1"""
        ).fetchall()
        assert len(dups) == 0

    def test_bridge_task_no_duplicates(self, onet_loaded_db):
        dups = onet_loaded_db.execute(
            """SELECT occupation_key, task_key, source_version, COUNT(*)
               FROM bridge_occupation_task
               GROUP BY occupation_key, task_key, source_version
               HAVING COUNT(*) > 1"""
        ).fetchall()
        assert len(dups) == 0

    def test_bridge_skill_occupation_ref(self, onet_loaded_db):
        orphans = onet_loaded_db.execute(
            """SELECT DISTINCT b.occupation_key FROM bridge_occupation_skill b
               WHERE b.occupation_key NOT IN (SELECT occupation_key FROM dim_occupation)"""
        ).fetchall()
        assert len(orphans) == 0

    def test_bridge_skill_skill_ref(self, onet_loaded_db):
        orphans = onet_loaded_db.execute(
            """SELECT DISTINCT b.skill_key FROM bridge_occupation_skill b
               WHERE b.skill_key NOT IN (SELECT skill_key FROM dim_skill)"""
        ).fetchall()
        assert len(orphans) == 0

    def test_bridge_knowledge_refs(self, onet_loaded_db):
        occ_orphans = onet_loaded_db.execute(
            """SELECT DISTINCT b.occupation_key FROM bridge_occupation_knowledge b
               WHERE b.occupation_key NOT IN (SELECT occupation_key FROM dim_occupation)"""
        ).fetchall()
        kn_orphans = onet_loaded_db.execute(
            """SELECT DISTINCT b.knowledge_key FROM bridge_occupation_knowledge b
               WHERE b.knowledge_key NOT IN (SELECT knowledge_key FROM dim_knowledge)"""
        ).fetchall()
        assert len(occ_orphans) == 0
        assert len(kn_orphans) == 0

    def test_bridge_ability_refs(self, onet_loaded_db):
        occ_orphans = onet_loaded_db.execute(
            """SELECT DISTINCT b.occupation_key FROM bridge_occupation_ability b
               WHERE b.occupation_key NOT IN (SELECT occupation_key FROM dim_occupation)"""
        ).fetchall()
        ab_orphans = onet_loaded_db.execute(
            """SELECT DISTINCT b.ability_key FROM bridge_occupation_ability b
               WHERE b.ability_key NOT IN (SELECT ability_key FROM dim_ability)"""
        ).fetchall()
        assert len(occ_orphans) == 0
        assert len(ab_orphans) == 0

    def test_bridge_task_refs(self, onet_loaded_db):
        occ_orphans = onet_loaded_db.execute(
            """SELECT DISTINCT b.occupation_key FROM bridge_occupation_task b
               WHERE b.occupation_key NOT IN (SELECT occupation_key FROM dim_occupation)"""
        ).fetchall()
        task_orphans = onet_loaded_db.execute(
            """SELECT DISTINCT b.task_key FROM bridge_occupation_task b
               WHERE b.task_key NOT IN (SELECT task_key FROM dim_task)"""
        ).fetchall()
        assert len(occ_orphans) == 0
        assert len(task_orphans) == 0


class TestOnetValidations:
    """T5-29, T5-30: Semantic and version alignment validations."""

    def test_structural_validations_pass(self, onet_loaded_db):
        for table in ["stage__onet__skills", "stage__onet__knowledge", "stage__onet__abilities", "stage__onet__tasks"]:
            results = validate_onet_structural(onet_loaded_db, table, RELEASE, min_rows=1)
            for r in results:
                assert r.passed, f"{r.check_name}: {r.message}"

    def test_occupation_mapping(self, onet_loaded_db):
        for table in ["stage__onet__skills", "stage__onet__knowledge", "stage__onet__abilities", "stage__onet__tasks"]:
            result = validate_onet_occupation_mapping(onet_loaded_db, table, RELEASE, SOC_VER)
            assert result.passed, f"{table}: {result.message}"

    def test_soc_alignment(self, onet_loaded_db):
        result = validate_onet_soc_alignment(onet_loaded_db, RELEASE, SOC_VER)
        assert result.passed, result.message


class TestOnetIdempotence:
    """T5-31, T5-32: Idempotent rerun tests."""

    def test_skills_rerun_no_duplicates(self, onet_loaded_db):
        before_dim = onet_loaded_db.execute("SELECT COUNT(*) FROM dim_skill").fetchone()[0]
        before_bridge = onet_loaded_db.execute("SELECT COUNT(*) FROM bridge_occupation_skill").fetchone()[0]
        load_dim_descriptor(onet_loaded_db, "dim_skill", "skill_key", "stage__onet__skills", ONET_VER)
        load_bridge_occupation_descriptor(
            onet_loaded_db,
            "bridge_occupation_skill",
            "dim_skill",
            "skill_key",
            "stage__onet__skills",
            ONET_VER,
            RELEASE,
            SOC_VER,
        )
        after_dim = onet_loaded_db.execute("SELECT COUNT(*) FROM dim_skill").fetchone()[0]
        after_bridge = onet_loaded_db.execute("SELECT COUNT(*) FROM bridge_occupation_skill").fetchone()[0]
        assert after_dim == before_dim
        assert after_bridge == before_bridge

    def test_full_rerun_no_duplicates(self, onet_loaded_db):
        counts_before = {}
        for table in [
            "dim_skill",
            "dim_knowledge",
            "dim_ability",
            "dim_task",
            "bridge_occupation_skill",
            "bridge_occupation_knowledge",
            "bridge_occupation_ability",
            "bridge_occupation_task",
        ]:
            counts_before[table] = onet_loaded_db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]

        # Rerun all dim loads
        load_dim_descriptor(onet_loaded_db, "dim_skill", "skill_key", "stage__onet__skills", ONET_VER)
        load_dim_descriptor(onet_loaded_db, "dim_knowledge", "knowledge_key", "stage__onet__knowledge", ONET_VER)
        load_dim_descriptor(onet_loaded_db, "dim_ability", "ability_key", "stage__onet__abilities", ONET_VER)
        load_dim_task(onet_loaded_db, ONET_VER)

        # Rerun all bridge loads
        load_bridge_occupation_descriptor(
            onet_loaded_db,
            "bridge_occupation_skill",
            "dim_skill",
            "skill_key",
            "stage__onet__skills",
            ONET_VER,
            RELEASE,
            SOC_VER,
        )
        load_bridge_occupation_descriptor(
            onet_loaded_db,
            "bridge_occupation_knowledge",
            "dim_knowledge",
            "knowledge_key",
            "stage__onet__knowledge",
            ONET_VER,
            RELEASE,
            SOC_VER,
        )
        load_bridge_occupation_descriptor(
            onet_loaded_db,
            "bridge_occupation_ability",
            "dim_ability",
            "ability_key",
            "stage__onet__abilities",
            ONET_VER,
            RELEASE,
            SOC_VER,
        )
        load_bridge_occupation_task(onet_loaded_db, ONET_VER, RELEASE, SOC_VER)

        for table, before in counts_before.items():
            after = onet_loaded_db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            assert after == before, f"{table}: {before} → {after}"
