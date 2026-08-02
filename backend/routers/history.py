"""History endpoint: GET /api/alerts/history."""

from typing import Optional

from fastapi import APIRouter

from database import get_db_conn, row_to_dict

router = APIRouter()


@router.get("/api/alerts/history")
async def get_history(
    unit_id: Optional[str] = None,
    system: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[int] = None,
    keyword: Optional[str] = None,
    page: int = 1,
    page_size: int = 10,
) -> dict:
    """Paginated alert history query with filters."""
    conn = get_db_conn()
    query = "SELECT * FROM alerts WHERE 1=1"
    params = []
    if unit_id:
        query += " AND unit_id = ?"
        params.append(unit_id)
    if system:
        query += " AND system = ?"
        params.append(system)
    if start_time:
        query += " AND triggered_at >= ?"
        params.append(start_time)
    if end_time:
        query += " AND triggered_at <= ?"
        params.append(end_time + " 23:59")
    if status:
        query += " AND processing_status = ?"
        params.append(status)
    if priority:
        query += " AND priority = ?"
        params.append(priority)
    if keyword:
        query += " AND content LIKE ?"
        params.append(f"%{keyword}%")

    count_query = f"SELECT COUNT(*) as cnt FROM ({query})"
    total = conn.execute(count_query, params).fetchone()["cnt"]

    query += " ORDER BY triggered_at DESC LIMIT ? OFFSET ?"
    params.extend([page_size, (page - 1) * page_size])
    rows = conn.execute(query, params).fetchall()

    conn.close()
    return {
        "list": [row_to_dict(r) for r in rows],
        "total": total,
        "page": page,
        "page_size": page_size,
    }
