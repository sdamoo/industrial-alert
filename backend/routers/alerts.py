"""Alert endpoints: GET /api/alerts, GET /api/alerts/{alert_id}."""

from fastapi import APIRouter, HTTPException

from database import get_db_conn, row_to_dict
from suggestions import get_suggestions

router = APIRouter()


@router.get("/api/alerts")
async def get_alerts() -> dict:
    """Get alert list with KPI statistics."""
    conn = get_db_conn()
    rows = conn.execute("SELECT * FROM alerts ORDER BY triggered_at DESC").fetchall()
    alerts = [row_to_dict(r) for r in rows]

    # KPI: count unclosed alerts grouped by system
    kpi_rows = conn.execute(
        """
        SELECT system, COUNT(*) as count FROM alerts
        WHERE is_closed = 0 GROUP BY system
    """
    ).fetchall()
    kpi = {r["system"]: r["count"] for r in kpi_rows}
    # Ensure all 6 systems are present (fill 0 for missing)
    for sys_name in [
        "齿轮箱系统",
        "发电机系统",
        "叶片系统",
        "变桨系统",
        "偏航系统",
        "液压系统",
    ]:
        kpi.setdefault(sys_name, 0)

    conn.close()
    return {"alerts": alerts, "kpi": kpi, "total": len(alerts)}


@router.get("/api/alerts/{alert_id}")
async def get_alert_detail(alert_id: str) -> dict:
    """Get a single alert detail with preset suggestions."""
    conn = get_db_conn()
    row = conn.execute(
        "SELECT * FROM alerts WHERE id = ?", (alert_id,)
    ).fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail=f"预警 ID 不存在: {alert_id}")

    alert = row_to_dict(row)
    alert["ai_suggestions"] = get_suggestions(alert["system"])
    conn.close()
    return alert
