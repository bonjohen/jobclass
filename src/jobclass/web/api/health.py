"""Health and metadata API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from jobclass.web.database import get_db

router = APIRouter(prefix="/api", tags=["system"])


@router.get("/health")
def health() -> dict:
    """Return warehouse health: status, version info, and table row counts."""
    conn = get_db()
    try:
        tables = [
            "dim_occupation", "dim_geography", "dim_industry",
            "dim_skill", "dim_knowledge", "dim_ability", "dim_task",
            "fact_occupation_employment_wages", "fact_occupation_projections",
        ]
        table_counts = {}
        for t in tables:
            try:
                count = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
                table_counts[t] = count
            except Exception:
                table_counts[t] = 0

        soc_version = None
        try:
            row = conn.execute(
                "SELECT DISTINCT soc_version FROM dim_occupation WHERE is_current = true LIMIT 1"
            ).fetchone()
            if row:
                soc_version = row[0]
        except Exception:
            pass

        return {
            "status": "ok",
            "warehouse_version": soc_version or "unknown",
            "table_counts": table_counts,
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.get("/stats")
def stats() -> dict:
    """Return key warehouse statistics for the landing page."""
    conn = get_db()
    try:
        result: dict = {}

        row = conn.execute("SELECT COUNT(*) FROM dim_occupation WHERE is_current = true").fetchone()
        result["occupation_count"] = row[0] if row else 0

        row = conn.execute("SELECT COUNT(*) FROM dim_geography WHERE is_current = true").fetchone()
        result["geography_count"] = row[0] if row else 0

        row = conn.execute("SELECT COUNT(DISTINCT source_dataset) FROM fact_occupation_employment_wages").fetchone()
        result["source_count"] = row[0] if row else 0

        row = conn.execute(
            "SELECT DISTINCT soc_version FROM dim_occupation WHERE is_current = true LIMIT 1"
        ).fetchone()
        result["soc_version"] = row[0] if row else None

        row = conn.execute(
            "SELECT COUNT(DISTINCT element_id) FROM dim_skill WHERE is_current = true"
        ).fetchone()
        result["skill_count"] = row[0] if row else 0

        row = conn.execute(
            "SELECT COUNT(DISTINCT task_id) FROM dim_task WHERE is_current = true"
        ).fetchone()
        result["task_count"] = row[0] if row else 0

        return result
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.get("/metadata")
def metadata() -> dict:
    """Return source versions, release IDs, and last load timestamps."""
    conn = get_db()
    try:
        result: dict = {}

        # SOC version
        row = conn.execute(
            "SELECT DISTINCT soc_version FROM dim_occupation WHERE is_current = true LIMIT 1"
        ).fetchone()
        result["soc_version"] = row[0] if row else None

        # OEWS release
        row = conn.execute(
            "SELECT DISTINCT source_release_id FROM fact_occupation_employment_wages LIMIT 1"
        ).fetchone()
        result["oews_release_id"] = row[0] if row else None

        # O*NET version
        row = conn.execute(
            "SELECT DISTINCT source_version FROM dim_skill WHERE is_current = true LIMIT 1"
        ).fetchone()
        result["onet_version"] = row[0] if row else None

        # Projections
        try:
            row = conn.execute(
                "SELECT DISTINCT projection_cycle FROM fact_occupation_projections LIMIT 1"
            ).fetchone()
            result["projections_cycle"] = row[0] if row else None
        except Exception:
            result["projections_cycle"] = None

        # Last load timestamp
        try:
            row = conn.execute(
                "SELECT MAX(completed_at) FROM run_manifest WHERE load_status = 'success'"
            ).fetchone()
            result["last_load_timestamp"] = str(row[0]) if row and row[0] else None
        except Exception:
            result["last_load_timestamp"] = None

        return result
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))
