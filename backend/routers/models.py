"""Model management endpoints (7 routes)."""

import os
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from database import get_db_conn
from model_scheduler import add_model_job, remove_model_job
# NOTE: absolute import — resolves to backend/models.py (top-level), NOT routers/models.py
from models import ModelUpdate, ToggleRequest

router = APIRouter()


def model_row_to_dict(row) -> dict:
    """Convert an ai_models row to dict."""
    return dict(row)


@router.get("/api/models")
async def get_models() -> dict:
    """Get model list."""
    conn = get_db_conn()
    rows = conn.execute("SELECT * FROM ai_models ORDER BY id").fetchall()
    models = [model_row_to_dict(r) for r in rows]
    conn.close()
    return {"models": models, "total": len(models)}


@router.post("/api/models")
async def upload_model(
    name: str = Form(...),
    component: str = Form(...),
    cycle: str = Form(...),
    description: Optional[str] = Form(None),
    file: UploadFile = File(...),
) -> dict:
    """Upload a new model file. Only .py files are allowed."""
    if not file.filename or not file.filename.endswith(".py"):
        raise HTTPException(status_code=400, detail="仅支持 .py 文件")

    os.makedirs("uploads", exist_ok=True)
    file_path = f"uploads/{file.filename}"
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    conn = get_db_conn()
    cursor = conn.execute(
        """
        INSERT INTO ai_models (name, component, cycle, file_path, status, description)
        VALUES (?, ?, ?, ?, '已停止', ?)
    """,
        (name, component, cycle, file_path, description),
    )
    conn.commit()

    model_id = cursor.lastrowid
    row = conn.execute(
        "SELECT * FROM ai_models WHERE id = ?", (model_id,)
    ).fetchone()
    conn.close()
    return model_row_to_dict(row)


@router.get("/api/models/{model_id}")
async def get_model_detail(model_id: int) -> dict:
    """Get a single model detail."""
    conn = get_db_conn()
    row = conn.execute(
        "SELECT * FROM ai_models WHERE id = ?", (model_id,)
    ).fetchone()
    if not row:
        conn.close()
        raise HTTPException(
            status_code=404, detail=f"模型 ID 不存在: {model_id}"
        )
    conn.close()
    return model_row_to_dict(row)


@router.put("/api/models/{model_id}")
async def update_model(model_id: int, body: ModelUpdate) -> dict:
    """Update model info. All fields are optional."""
    conn = get_db_conn()
    row = conn.execute(
        "SELECT * FROM ai_models WHERE id = ?", (model_id,)
    ).fetchone()
    if not row:
        conn.close()
        raise HTTPException(
            status_code=404, detail=f"模型 ID 不存在: {model_id}"
        )

    updates = []
    params = []
    for field in ["name", "component", "cycle", "status", "description"]:
        val = getattr(body, field)
        if val is not None:
            updates.append(f"{field} = ?")
            params.append(val)

    if updates:
        updates.append("updated_at = ?")
        params.append(datetime.now().strftime("%Y-%m-%d %H:%M"))
        params.append(model_id)
        conn.execute(
            f"UPDATE ai_models SET {', '.join(updates)} WHERE id = ?", params
        )
        conn.commit()

    row = conn.execute(
        "SELECT * FROM ai_models WHERE id = ?", (model_id,)
    ).fetchone()
    conn.close()
    return model_row_to_dict(row)


@router.delete("/api/models/{model_id}")
async def delete_model(model_id: int) -> dict:
    """Delete a model: remove scheduled job + DB record + uploaded file."""
    conn = get_db_conn()
    row = conn.execute(
        "SELECT * FROM ai_models WHERE id = ?", (model_id,)
    ).fetchone()
    if not row:
        conn.close()
        raise HTTPException(
            status_code=404, detail=f"模型 ID 不存在: {model_id}"
        )

    file_path = row["file_path"]

    # Remove scheduled job first
    remove_model_job(model_id)

    conn.execute("DELETE FROM ai_models WHERE id = ?", (model_id,))
    conn.commit()
    conn.close()

    # Delete uploaded file
    if file_path and os.path.exists(file_path):
        os.remove(file_path)

    return {"id": model_id, "message": "模型已删除"}


@router.post("/api/models/{model_id}/run")
async def run_model(model_id: int) -> dict:
    """Manually trigger model run, update last_run_at."""
    conn = get_db_conn()
    row = conn.execute(
        "SELECT * FROM ai_models WHERE id = ?", (model_id,)
    ).fetchone()
    if not row:
        conn.close()
        raise HTTPException(
            status_code=404, detail=f"模型 ID 不存在: {model_id}"
        )

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    conn.execute(
        "UPDATE ai_models SET last_run_at = ?, status = '运行中', updated_at = ? WHERE id = ?",
        (now_str, now_str, model_id),
    )
    conn.commit()
    conn.close()

    return {
        "id": model_id,
        "status": "运行中",
        "message": "模型已触发运行",
        "last_run_at": now_str,
    }


@router.post("/api/models/{model_id}/toggle")
async def toggle_model(model_id: int, body: ToggleRequest) -> dict:
    """Start or stop a model's scheduled job."""
    conn = get_db_conn()
    row = conn.execute(
        "SELECT * FROM ai_models WHERE id = ?", (model_id,)
    ).fetchone()
    if not row:
        conn.close()
        raise HTTPException(
            status_code=404, detail=f"模型 ID 不存在: {model_id}"
        )

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

    if body.action == "start":
        add_model_job(model_id, row["cycle"], row["file_path"])
        conn.execute(
            "UPDATE ai_models SET status = '运行中', updated_at = ? WHERE id = ?",
            (now_str, model_id),
        )
        message = "模型已启动"
        status = "运行中"
    elif body.action == "stop":
        remove_model_job(model_id)
        conn.execute(
            "UPDATE ai_models SET status = '已停止', updated_at = ? WHERE id = ?",
            (now_str, model_id),
        )
        message = "模型已停止"
        status = "已停止"
    else:
        conn.close()
        raise HTTPException(
            status_code=400, detail="action 仅支持 'start' 或 'stop'"
        )

    conn.commit()
    conn.close()

    return {"id": model_id, "status": status, "message": message}
