"""Work order endpoint: POST /api/work-orders (idempotent)."""

from fastapi import APIRouter, HTTPException

from database import get_db_conn
# NOTE: absolute import — resolves to backend/models.py (top-level), NOT routers/models.py
from models import WorkOrderRequest
from suggestions import get_suggestions

router = APIRouter()


@router.post("/api/work-orders")
async def create_work_order(req: WorkOrderRequest) -> dict:
    """Create a work order (idempotent: same alert_id returns existing order)."""
    conn = get_db_conn()

    # Idempotency check
    existing = conn.execute(
        "SELECT * FROM work_orders WHERE alert_id = ?", (req.alert_id,)
    ).fetchone()
    if existing:
        conn.close()
        return {
            "id": existing["id"],
            "alert_id": req.alert_id,
            "status": "created",
            "message": "该预警已生成工单，不重复创建",
        }

    alert = conn.execute(
        "SELECT * FROM alerts WHERE id = ?", (req.alert_id,)
    ).fetchone()
    if not alert:
        conn.close()
        raise HTTPException(
            status_code=404, detail=f"预警 ID 不存在: {req.alert_id}"
        )

    suggestions = get_suggestions(alert["system"])
    cursor = conn.execute(
        """
        INSERT INTO work_orders (alert_id, unit_id, system, location, content,
            triggered_at, suggested_inspect_time, priority, estimated_hours,
            ai_measures, ai_personnel, ai_tools, ai_materials)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
    """,
        (
            alert["id"],
            alert["unit_id"],
            alert["system"],
            alert["location"],
            alert["content"],
            alert["triggered_at"],
            alert["suggested_inspect_time"],
            alert["priority"],
            alert["estimated_hours"],
            suggestions["measures"],
            suggestions["personnel"],
            suggestions["tools"],
            suggestions["materials"],
        ),
    )

    # Sync alert has_work_order flag
    conn.execute(
        "UPDATE alerts SET has_work_order = 1 WHERE id = ?", (req.alert_id,)
    )
    conn.commit()
    conn.close()

    return {
        "id": cursor.lastrowid,
        "alert_id": req.alert_id,
        "status": "created",
        "message": "工单已生成",
    }
