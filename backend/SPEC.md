# 后端开发规格书 — 风电设备预警模块

> **必读文件**（按顺序）：
> 1. `../API_CONTRACT.md` — 接口契约（字段定义、接口格式）
> 2. 本文件 — 数据库设计、种子数据、预设建议、接口实现要点
> 3. `AGENTS.md` — 后端 AI 编码规范

---

## 一、项目目录结构

```
wind-warning-backend/
├── main.py                  # FastAPI 入口，挂载所有路由 + CORS + APScheduler
├── database.py              # SQLite 连接 + 建表（3 张表）
├── models.py                # Pydantic 数据模型
├── seed.py                  # 种子数据脚本（11 alerts + 2 models）
├── suggestions.py           # 预设建议模板（6 个风电系统）
├── model_scheduler.py       # APScheduler 定时任务调度
├── routers/
│   ├── alerts.py            # GET /api/alerts, GET /api/alerts/:id
│   ├── history.py           # GET /api/alerts/history
│   ├── work_orders.py       # POST /api/work-orders
│   └── models.py            # 模型管理 7 个接口
├── uploads/                 # 模型文件上传目录
├── data/                    # SQLite 文件目录（运行时生成）
├── requirements.txt
└── .env
```

---

## 二、数据库表结构（SQLite）

### 2.1 alerts 表

```sql
CREATE TABLE IF NOT EXISTS alerts (
    id              TEXT PRIMARY KEY,
    unit_id         TEXT NOT NULL,
    system          TEXT NOT NULL,
    location        TEXT NOT NULL,
    content         TEXT NOT NULL,
    triggered_at    TEXT NOT NULL,
    suggested_inspect_time TEXT,
    priority        INTEGER NOT NULL DEFAULT 3,
    estimated_hours REAL DEFAULT 2.0,
    processing_status TEXT NOT NULL DEFAULT '待处理',
    is_closed       INTEGER NOT NULL DEFAULT 0,
    treatment_measures TEXT,
    has_work_order  INTEGER NOT NULL DEFAULT 0,
    created_at      TEXT DEFAULT (datetime('now','localtime'))
);

CREATE INDEX IF NOT EXISTS idx_alerts_system ON alerts(system);
CREATE INDEX IF NOT EXISTS idx_alerts_priority ON alerts(priority);
CREATE INDEX IF NOT EXISTS idx_alerts_status ON alerts(processing_status);
CREATE INDEX IF NOT EXISTS idx_alerts_triggered ON alerts(triggered_at);
```

### 2.2 work_orders 表

```sql
CREATE TABLE IF NOT EXISTS work_orders (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    alert_id        TEXT NOT NULL UNIQUE,
    unit_id         TEXT NOT NULL,
    system          TEXT NOT NULL,
    location        TEXT NOT NULL,
    content         TEXT NOT NULL,
    triggered_at    TEXT NOT NULL,
    suggested_inspect_time TEXT,
    priority        INTEGER NOT NULL,
    estimated_hours REAL,
    ai_measures     TEXT,
    ai_personnel    TEXT,
    ai_tools        TEXT,
    ai_materials    TEXT,
    actual_inspect_time  TEXT,
    inspect_process TEXT,
    inspect_result  TEXT,
    status          TEXT NOT NULL DEFAULT 'created',
    created_at      TEXT DEFAULT (datetime('now','localtime')),
    FOREIGN KEY (alert_id) REFERENCES alerts(id)
);
```

### 2.3 ai_models 表

```sql
CREATE TABLE IF NOT EXISTS ai_models (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL,
    component       TEXT NOT NULL,
    cycle           TEXT NOT NULL,
    file_path       TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT '已停止',
    description     TEXT,
    last_run_at     TEXT,
    created_at      TEXT DEFAULT (datetime('now','localtime')),
    updated_at      TEXT DEFAULT (datetime('now','localtime'))
);
```

### 2.4 字段转换约定

SQLite 中 `is_closed` 和 `has_work_order` 存为 `INTEGER`（0/1），**API 返回时必须转为 `boolean`**：

```python
def row_to_dict(row):
    d = dict(row)
    d['is_closed'] = bool(d['is_closed'])
    d['has_work_order'] = bool(d['has_work_order'])
    return d
```

---

## 三、预设建议模板

```python
# suggestions.py

PRESET_SUGGESTIONS = {
    "齿轮箱系统": {
        "measures": "1.检查齿轮油品质及油位 2.核实轴承温度测点 3.检查冷却系统运行状态 4.必要时降功率运行",
        "personnel": "齿轮箱检修工2人、状态监测工程师1人",
        "tools": "振动分析仪、油液检测仪、红外测温仪",
        "materials": "齿轮油、密封件、备用轴承"
    },
    "发电机系统": {
        "measures": "1.检查冷却系统流量 2.核实温度测点 3.检查绝缘电阻 4.监测轴承振动",
        "personnel": "发电机检修工2人、电气工程师1人",
        "tools": "兆欧表、红外热像仪、振动检测仪",
        "materials": "绝缘材料、密封件、润滑油"
    },
    "叶片系统": {
        "measures": "1.目视检查叶片表面 2.使用无人机巡检裂纹 3.检查防雷装置 4.必要时停机修复",
        "personnel": "叶片检修工2人、无人机操作员1人",
        "tools": "无人机、探伤仪、游标卡尺",
        "materials": "叶片修补材料、防雷器件、密封胶"
    },
    "变桨系统": {
        "measures": "1.检查变桨轴承磨损 2.核实变桨电机温度 3.检查变桨角度传感器 4.校准变桨限位",
        "personnel": "变桨系统检修工2人",
        "tools": "角度测量仪、振动检测仪、万用表",
        "materials": "备用变桨电机、轴承、传感器"
    },
    "偏航系统": {
        "measures": "1.检查偏航轴承磨损 2.核实偏航电机电流 3.检查偏航计数器 4.润滑偏航齿圈",
        "personnel": "偏航系统检修工2人",
        "tools": "电流钳形表、振动检测仪、润滑脂加注枪",
        "materials": "润滑脂、密封件、备用偏航电机"
    },
    "液压系统": {
        "measures": "1.检查液压油温及油位 2.核实系统压力 3.检查管路接头泄漏 4.更换液压油滤芯",
        "personnel": "液压系统检修工2人",
        "tools": "压力表、红外测温仪、泄漏检测仪",
        "materials": "液压油、滤芯、密封件、管接头"
    }
}

def get_suggestions(system: str) -> dict:
    """根据系统名称返回预设建议。"""
    return PRESET_SUGGESTIONS.get(system, {
        "measures": "请联系相关技术人员进行检查",
        "personnel": "检修工2人",
        "tools": "常规检修工具",
        "materials": "常规备件"
    })
```

---

## 四、种子数据

```python
# seed.py

import sqlite3

SEED_ALERTS = [
    ("W001", "风机A001", "齿轮箱系统", "高速轴轴承",
     "高速轴轴承温度超标，实测85℃，限值80℃，超温5℃，持续10分钟",
     "2026-07-31 14:30", "2026-07-31 16:00", 1, 4.0, "待处理", 0, "检查齿轮油品质及油位，核实轴承温度测点", 0),
    ("W002", "风机A001", "发电机系统", "定子绕组",
     "定子绕组温度偏高，实测118℃，限值120℃，接近预警线",
     "2026-07-31 14:15", "2026-07-31 15:00", 2, 3.0, "处理中", 0, "检查冷却系统流量，核实温度测点", 0),
    ("W003", "风机A003", "齿轮箱系统", "中速轴齿轮",
     "齿面磨损量0.8mm，预警阈值0.5mm，需评估剩余寿命",
     "2026-07-31 13:50", "2026-07-31 15:30", 1, 6.0, "待处理", 0, "齿面测厚复检，评估剩余寿命", 0),
    ("W004", "风机A003", "叶片系统", "1号叶片",
     "叶片表面裂纹检测，长度约15cm，需评估扩展风险",
     "2026-07-31 13:20", "2026-07-31 14:30", 3, 2.0, "待处理", 0, "无人机巡检裂纹，评估扩展风险", 0),
    ("W005", "风机A005", "变桨系统", "变桨轴承",
     "变桨轴承振动异常，实测7.5mm/s，限值4.5mm/s",
     "2026-07-31 12:40", "2026-07-31 14:00", 2, 3.0, "处理中", 0, "检查变桨轴承磨损，核实振动值", 0),
    ("W006", "风机A005", "偏航系统", "偏航轴承",
     "偏航轴承磨损量超限，实测间隙1.2mm，限值0.8mm",
     "2026-07-31 11:30", "2026-07-31 13:00", 3, 2.0, "已完成", 1, "已检查偏航轴承磨损，记录存档", 0),
    ("W007", "风机A007", "齿轮箱系统", "低速轴轴承",
     "润滑油压偏低，实测0.8bar，限值1.5bar",
     "2026-07-31 10:15", "2026-07-31 12:00", 2, 4.0, "待处理", 0, "检查润滑油压，核实管路密封", 0),
    ("W008", "风机A007", "液压系统", "液压站",
     "液压油温超标，实测65℃，限值55℃，持续20分钟",
     "2026-07-31 09:00", "2026-07-31 10:30", 3, 2.0, "待处理", 0, "检查液压油温及冷却系统", 0),
    ("W009", "风机A001", "发电机系统", "前轴承",
     "轴承振动超标，实测125μm，限值100μm，持续8分钟",
     "2026-07-31 08:45", "2026-07-31 10:00", 1, 3.0, "处理中", 0, "检查轴承振动，核实润滑状态", 0),
    ("W010", "风机A003", "叶片系统", "2号叶片",
     "叶片零位偏差2.5°，限值2°，需校准零位",
     "2026-07-30 22:30", "2026-07-31 08:00", 2, 2.0, "待处理", 0, "校准叶片零位", 0),
    ("W011", "风机A005", "变桨系统", "变桨电机",
     "变桨电机过热保护动作，温度92℃，限值85℃",
     "2026-07-30 16:00", "2026-07-30 18:00", 3, 1.5, "已完成", 1, "已检查变桨电机冷却，恢复正常", 0),
]

SEED_MODELS = [
    ("叶片零位预警模型", "叶片系统", "每日", "uploads/blade_zero_model.py", "运行中",
     "基于SCADA数据的叶片零位偏差检测模型", "2026-07-31 06:00", "2026-07-30 10:00", "2026-07-31 06:00"),
    ("齿轮箱温度预警模型", "齿轮箱系统", "每小时", "uploads/gearbox_temp_model.py", "已停止",
     "基于温度趋势的齿轮箱健康度评估模型", None, "2026-07-30 14:00", "2026-07-30 14:00"),
]

def seed():
    import os
    os.makedirs("data", exist_ok=True)
    os.makedirs("uploads", exist_ok=True)
    conn = sqlite3.connect("data/wind_warning.db")
    conn.row_factory = sqlite3.Row

    # 建表（同 database.py 中的 SQL）
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS alerts (
            id              TEXT PRIMARY KEY,
            unit_id         TEXT NOT NULL,
            system          TEXT NOT NULL,
            location        TEXT NOT NULL,
            content         TEXT NOT NULL,
            triggered_at    TEXT NOT NULL,
            suggested_inspect_time TEXT,
            priority        INTEGER NOT NULL DEFAULT 3,
            estimated_hours REAL DEFAULT 2.0,
            processing_status TEXT NOT NULL DEFAULT '待处理',
            is_closed       INTEGER NOT NULL DEFAULT 0,
            treatment_measures TEXT,
            has_work_order  INTEGER NOT NULL DEFAULT 0,
            created_at      TEXT DEFAULT (datetime('now','localtime'))
        );
        CREATE TABLE IF NOT EXISTS work_orders (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            alert_id        TEXT NOT NULL UNIQUE,
            unit_id         TEXT NOT NULL,
            system          TEXT NOT NULL,
            location        TEXT NOT NULL,
            content         TEXT NOT NULL,
            triggered_at    TEXT NOT NULL,
            suggested_inspect_time TEXT,
            priority        INTEGER NOT NULL,
            estimated_hours REAL,
            ai_measures     TEXT,
            ai_personnel    TEXT,
            ai_tools        TEXT,
            ai_materials    TEXT,
            actual_inspect_time  TEXT,
            inspect_process TEXT,
            inspect_result  TEXT,
            status          TEXT NOT NULL DEFAULT 'created',
            created_at      TEXT DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (alert_id) REFERENCES alerts(id)
        );
        CREATE TABLE IF NOT EXISTS ai_models (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            name            TEXT NOT NULL,
            component       TEXT NOT NULL,
            cycle           TEXT NOT NULL,
            file_path       TEXT NOT NULL,
            status          TEXT NOT NULL DEFAULT '已停止',
            description     TEXT,
            last_run_at     TEXT,
            created_at      TEXT DEFAULT (datetime('now','localtime')),
            updated_at      TEXT DEFAULT (datetime('now','localtime'))
        );
    """)

    conn.executemany("""
        INSERT OR REPLACE INTO alerts
        (id, unit_id, system, location, content, triggered_at, suggested_inspect_time,
         priority, estimated_hours, processing_status, is_closed, treatment_measures, has_work_order)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, SEED_ALERTS)

    conn.executemany("""
        INSERT OR REPLACE INTO ai_models
        (name, component, cycle, file_path, status, description, last_run_at, created_at, updated_at)
        VALUES (?,?,?,?,?,?,?,?,?)
    """, SEED_MODELS)

    conn.commit()
    conn.close()
    print("种子数据插入完成：11 条预警 + 2 条模型")

if __name__ == "__main__":
    seed()
```

---

## 五、预警接口实现要点

### 5.1 GET /api/alerts

```python
# routers/alerts.py

from fastapi import APIRouter, HTTPException
from database import get_db_conn
from suggestions import get_suggestions

router = APIRouter()


def row_to_dict(row):
    d = dict(row)
    d['is_closed'] = bool(d['is_closed'])
    d['has_work_order'] = bool(d['has_work_order'])
    return d


@router.get("/api/alerts")
async def get_alerts() -> dict:
    """获取预警列表 + KPI 统计。"""
    conn = get_db_conn()
    rows = conn.execute("SELECT * FROM alerts ORDER BY triggered_at DESC").fetchall()
    alerts = [row_to_dict(r) for r in rows]

    # KPI 统计：仅统计 is_closed = 0 的预警，按 system 分组
    kpi_rows = conn.execute("""
        SELECT system, COUNT(*) as count FROM alerts
        WHERE is_closed = 0 GROUP BY system
    """).fetchall()
    kpi = {r['system']: r['count'] for r in kpi_rows}
    # 补全 6 个系统的 0 值
    for sys_name in ['齿轮箱系统', '发电机系统', '叶片系统', '变桨系统', '偏航系统', '液压系统']:
        kpi.setdefault(sys_name, 0)

    conn.close()
    return {"alerts": alerts, "kpi": kpi, "total": len(alerts)}
```

### 5.2 GET /api/alerts/:id

```python
@router.get("/api/alerts/{alert_id}")
async def get_alert_detail(alert_id: str) -> dict:
    """获取单条预警详情，含预设建议。"""
    conn = get_db_conn()
    row = conn.execute("SELECT * FROM alerts WHERE id = ?", (alert_id,)).fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail=f"预警 ID 不存在: {alert_id}")

    alert = row_to_dict(row)
    # 根据 system 字段匹配预设建议
    alert['ai_suggestions'] = get_suggestions(alert['system'])
    conn.close()
    return alert
```

### 5.3 GET /api/alerts/history

```python
# routers/history.py

from fastapi import APIRouter
from database import get_db_conn

router = APIRouter()


@router.get("/api/alerts/history")
async def get_history(
    unit_id: str = None,
    system: str = None,
    start_time: str = None,
    end_time: str = None,
    status: str = None,
    priority: int = None,
    keyword: str = None,
    page: int = 1,
    page_size: int = 10,
) -> dict:
    """分页查询预警历史。"""
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
    total = conn.execute(count_query, params).fetchone()['cnt']

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
```

### 5.4 POST /api/work-orders

```python
# routers/work_orders.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from database import get_db_conn
from suggestions import get_suggestions

router = APIRouter()


class WorkOrderRequest(BaseModel):
    alert_id: str


@router.post("/api/work-orders")
async def create_work_order(req: WorkOrderRequest) -> dict:
    """生成工单（幂等）。"""
    conn = get_db_conn()
    # 幂等检查
    existing = conn.execute(
        "SELECT * FROM work_orders WHERE alert_id = ?", (req.alert_id,)
    ).fetchone()
    if existing:
        conn.close()
        return {
            "id": existing['id'],
            "alert_id": req.alert_id,
            "status": "created",
            "message": "该预警已生成工单，不重复创建",
        }

    alert = conn.execute(
        "SELECT * FROM alerts WHERE id = ?", (req.alert_id,)
    ).fetchone()
    if not alert:
        conn.close()
        raise HTTPException(status_code=404, detail=f"预警 ID 不存在: {req.alert_id}")

    suggestions = get_suggestions(alert['system'])
    cursor = conn.execute("""
        INSERT INTO work_orders (alert_id, unit_id, system, location, content,
            triggered_at, suggested_inspect_time, priority, estimated_hours,
            ai_measures, ai_personnel, ai_tools, ai_materials)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        alert['id'], alert['unit_id'], alert['system'], alert['location'],
        alert['content'], alert['triggered_at'], alert['suggested_inspect_time'],
        alert['priority'], alert['estimated_hours'],
        suggestions['measures'], suggestions['personnel'],
        suggestions['tools'], suggestions['materials'],
    ))

    # 同步更新 alerts 表的 has_work_order
    conn.execute("UPDATE alerts SET has_work_order = 1 WHERE id = ?", (req.alert_id,))
    conn.commit()
    conn.close()

    return {
        "id": cursor.lastrowid,
        "alert_id": req.alert_id,
        "status": "created",
        "message": "工单已生成",
    }
```

---

## 六、模型管理接口实现要点

### 6.1 GET /api/models — 获取模型列表

```python
# routers/models.py

import os
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from database import get_db_conn
from model_scheduler import scheduler, add_model_job, remove_model_job
from datetime import datetime

router = APIRouter()


def model_row_to_dict(row):
    """将 ai_models 行转为字典。"""
    d = dict(row)
    return d


@router.get("/api/models")
async def get_models() -> dict:
    """获取模型列表。"""
    conn = get_db_conn()
    rows = conn.execute("SELECT * FROM ai_models ORDER BY id").fetchall()
    models = [model_row_to_dict(r) for r in rows]
    conn.close()
    return {"models": models, "total": len(models)}
```

### 6.2 POST /api/models — 上传新模型

```python
@router.post("/api/models")
async def upload_model(
    name: str = Form(...),
    component: str = Form(...),
    cycle: str = Form(...),
    description: str = Form(None),
    file: UploadFile = File(...),
) -> dict:
    """上传新模型文件并创建记录。仅支持 .py 文件。"""
    # 校验文件扩展名
    if not file.filename or not file.filename.endswith(".py"):
        raise HTTPException(status_code=400, detail="仅支持 .py 文件")

    # 确保上传目录存在
    os.makedirs("uploads", exist_ok=True)

    # 保存文件
    file_path = f"uploads/{file.filename}"
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    conn = get_db_conn()
    cursor = conn.execute("""
        INSERT INTO ai_models (name, component, cycle, file_path, status, description)
        VALUES (?, ?, ?, ?, '已停止', ?)
    """, (name, component, cycle, file_path, description))
    conn.commit()

    model_id = cursor.lastrowid
    row = conn.execute("SELECT * FROM ai_models WHERE id = ?", (model_id,)).fetchone()
    conn.close()
    return model_row_to_dict(row)
```

### 6.3 GET /api/models/:id — 获取模型详情

```python
@router.get("/api/models/{model_id}")
async def get_model_detail(model_id: int) -> dict:
    """获取单个模型详情。"""
    conn = get_db_conn()
    row = conn.execute("SELECT * FROM ai_models WHERE id = ?", (model_id,)).fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail=f"模型 ID 不存在: {model_id}")
    conn.close()
    return model_row_to_dict(row)
```

### 6.4 PUT /api/models/:id — 更新模型信息

```python
class ModelUpdate(BaseModel):
    name: str = None
    component: str = None
    cycle: str = None
    status: str = None
    description: str = None


@router.put("/api/models/{model_id}")
async def update_model(model_id: int, body: ModelUpdate) -> dict:
    """更新模型信息。所有字段可选。"""
    conn = get_db_conn()
    row = conn.execute("SELECT * FROM ai_models WHERE id = ?", (model_id,)).fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail=f"模型 ID 不存在: {model_id}")

    updates = []
    params = []
    for field in ['name', 'component', 'cycle', 'status', 'description']:
        val = getattr(body, field)
        if val is not None:
            updates.append(f"{field} = ?")
            params.append(val)

    if updates:
        updates.append("updated_at = ?")
        params.append(datetime.now().strftime("%Y-%m-%d %H:%M"))
        params.append(model_id)
        conn.execute(f"UPDATE ai_models SET {', '.join(updates)} WHERE id = ?", params)
        conn.commit()

    row = conn.execute("SELECT * FROM ai_models WHERE id = ?", (model_id,)).fetchone()
    conn.close()
    return model_row_to_dict(row)
```

### 6.5 DELETE /api/models/:id — 删除模型

```python
@router.delete("/api/models/{model_id}")
async def delete_model(model_id: int) -> dict:
    """删除模型记录，同时移除定时任务并可选择删除文件。"""
    conn = get_db_conn()
    row = conn.execute("SELECT * FROM ai_models WHERE id = ?", (model_id,)).fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail=f"模型 ID 不存在: {model_id}")

    file_path = row['file_path']

    # 移除定时任务（如果存在）
    remove_model_job(model_id)

    # 删除数据库记录
    conn.execute("DELETE FROM ai_models WHERE id = ?", (model_id,))
    conn.commit()
    conn.close()

    # 删除上传的模型文件（如果存在）
    if file_path and os.path.exists(file_path):
        os.remove(file_path)

    return {"id": model_id, "message": "模型已删除"}
```

### 6.6 POST /api/models/:id/run — 手动运行模型

```python
@router.post("/api/models/{model_id}/run")
async def run_model(model_id: int) -> dict:
    """手动触发模型运行，更新 last_run_at。"""
    conn = get_db_conn()
    row = conn.execute("SELECT * FROM ai_models WHERE id = ?", (model_id,)).fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail=f"模型 ID 不存在: {model_id}")

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
```

### 6.7 POST /api/models/:id/toggle — 启停模型

```python
class ToggleRequest(BaseModel):
    action: str  # "start" 或 "stop"


@router.post("/api/models/{model_id}/toggle")
async def toggle_model(model_id: int, body: ToggleRequest) -> dict:
    """启动或停止模型的定时调度任务。"""
    conn = get_db_conn()
    row = conn.execute("SELECT * FROM ai_models WHERE id = ?", (model_id,)).fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail=f"模型 ID 不存在: {model_id}")

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

    if body.action == "start":
        # 添加定时任务
        add_model_job(model_id, row['cycle'], row['file_path'])
        conn.execute(
            "UPDATE ai_models SET status = '运行中', updated_at = ? WHERE id = ?",
            (now_str, model_id),
        )
        message = "模型已启动"
        status = "运行中"
    elif body.action == "stop":
        # 移除定时任务
        remove_model_job(model_id)
        conn.execute(
            "UPDATE ai_models SET status = '已停止', updated_at = ? WHERE id = ?",
            (now_str, model_id),
        )
        message = "模型已停止"
        status = "已停止"
    else:
        conn.close()
        raise HTTPException(status_code=400, detail="action 仅支持 'start' 或 'stop'")

    conn.commit()
    conn.close()

    return {"id": model_id, "status": status, "message": message}
```

---

## 七、APScheduler 配置

```python
# model_scheduler.py

import sqlite3
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

# 全局调度器实例
scheduler = BackgroundScheduler()

# 运行周期 → CronTrigger 映射
CYCLE_TRIGGER_MAP = {
    "每小时": CronTrigger(minute=0),           # 每整点执行
    "每日": CronTrigger(hour=6, minute=0),      # 每日 06:00 执行
    "每周": CronTrigger(day_of_week="mon", hour=6, minute=0),  # 每周一 06:00
    "每月": CronTrigger(day=1, hour=6, minute=0),              # 每月 1 日 06:00
}


def run_model_job(model_id: int, file_path: str):
    """定时任务回调函数：执行模型并更新 last_run_at。"""
    try:
        # 模型执行逻辑（此处为模拟执行，不执行上传文件中的危险代码）
        # 实际场景中可在此处加载并调用模型文件的 main 函数
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

        conn = sqlite3.connect("data/wind_warning.db")
        conn.row_factory = sqlite3.Row
        conn.execute(
            "UPDATE ai_models SET last_run_at = ?, updated_at = ? WHERE id = ?",
            (now_str, now_str, model_id),
        )
        conn.commit()
        conn.close()
        print(f"[Scheduler] 模型 {model_id} 已执行，文件: {file_path}")
    except Exception as e:
        print(f"[Scheduler] 模型 {model_id} 执行失败: {e}")


def add_model_job(model_id: int, cycle: str, file_path: str):
    """为模型添加定时调度任务。"""
    trigger = CYCLE_TRIGGER_MAP.get(cycle)
    if trigger is None:
        print(f"[Scheduler] 未知的运行周期: {cycle}，跳过调度")
        return

    # 先移除已有任务（避免重复）
    remove_model_job(model_id)

    job_id = f"model_{model_id}"
    scheduler.add_job(
        run_model_job,
        trigger=trigger,
        args=[model_id, file_path],
        id=job_id,
        replace_existing=True,
    )
    print(f"[Scheduler] 已添加定时任务: {job_id}，周期: {cycle}")


def remove_model_job(model_id: int):
    """移除模型的定时调度任务。"""
    job_id = f"model_{model_id}"
    try:
        scheduler.remove_job(job_id)
        print(f"[Scheduler] 已移除定时任务: {job_id}")
    except Exception:
        # 任务不存在时静默处理
        pass


def restore_running_jobs():
    """应用启动时恢复所有状态为'运行中'的模型定时任务。"""
    conn = sqlite3.connect("data/wind_warning.db")
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT id, cycle, file_path FROM ai_models WHERE status = '运行中'"
    ).fetchall()
    conn.close()

    for row in rows:
        add_model_job(row['id'], row['cycle'], row['file_path'])
    print(f"[Scheduler] 已恢复 {len(rows)} 个运行中的模型任务")


def start_scheduler():
    """启动调度器。"""
    if not scheduler.running:
        scheduler.start()
        print("[Scheduler] 调度器已启动")


def shutdown_scheduler():
    """关闭调度器。"""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        print("[Scheduler] 调度器已关闭")
```

---

## 八、main.py 入口

```python
# main.py

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import alerts, history, work_orders, models
from database import init_db
from model_scheduler import start_scheduler, shutdown_scheduler, restore_running_jobs

app = FastAPI(title="风电设备预警模块 API")

# CORS（联调用）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载所有路由
# 注意：history.router 必须在 alerts.router 之前挂载，
# 否则 /api/alerts/history 会被 /api/alerts/{alert_id} 路由先匹配到
app.include_router(history.router)
app.include_router(alerts.router)
app.include_router(work_orders.router)
app.include_router(models.router)


@app.on_event("startup")
async def startup():
    # 确保目录存在
    os.makedirs("data", exist_ok=True)
    os.makedirs("uploads", exist_ok=True)
    # 初始化数据库
    init_db()
    # 启动 APScheduler 并恢复运行中的模型任务
    start_scheduler()
    restore_running_jobs()


@app.on_event("shutdown")
async def shutdown():
    # 关闭 APScheduler
    shutdown_scheduler()


@app.get("/")
async def root() -> dict:
    return {"message": "风电设备预警模块 API", "docs": "/docs"}
```

---

## 九、环境配置

### .env

```env
DB_PATH=./data/wind_warning.db
HOST=0.0.0.0
PORT=8000
```

### requirements.txt

```
fastapi==0.111.0
uvicorn[standard]==0.30.1
pydantic==2.7.1
python-dotenv==1.0.1
apscheduler==3.10.4
python-multipart==0.0.9
```

### 启动命令

```bash
pip install -r requirements.txt
python seed.py          # 初始化数据库 + 种子数据（11 条预警 + 2 条模型）
uvicorn main:app --reload --host 0.0.0.0 --port 8000
# Swagger 文档：http://localhost:8000/docs
```

---

## 十、补充说明（开工前修正项）

> 以下是对前文代码块的修正和补充，开发时以本节为准。

### 10.1 database.py 完整实现

前文路由代码调用了 `get_db_conn()`、`init_db()`、`row_to_dict()`，但未给出 `database.py` 的完整代码。实现如下：

```python
# database.py

import os
import sqlite3
from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.getenv("DB_PATH", "./data/wind_warning.db")


def get_db_conn() -> sqlite3.Connection:
    """Create and return a SQLite connection with Row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Initialize database: create tables and indexes if not exist."""
    db_dir = os.path.dirname(DB_PATH)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
    conn = get_db_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS alerts (
            id              TEXT PRIMARY KEY,
            unit_id         TEXT NOT NULL,
            system          TEXT NOT NULL,
            location        TEXT NOT NULL,
            content         TEXT NOT NULL,
            triggered_at    TEXT NOT NULL,
            suggested_inspect_time TEXT,
            priority        INTEGER NOT NULL DEFAULT 3,
            estimated_hours REAL DEFAULT 2.0,
            processing_status TEXT NOT NULL DEFAULT '待处理',
            is_closed       INTEGER NOT NULL DEFAULT 0,
            treatment_measures TEXT,
            has_work_order  INTEGER NOT NULL DEFAULT 0,
            created_at      TEXT DEFAULT (datetime('now','localtime'))
        );
        CREATE TABLE IF NOT EXISTS work_orders (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            alert_id        TEXT NOT NULL UNIQUE,
            unit_id         TEXT NOT NULL,
            system          TEXT NOT NULL,
            location        TEXT NOT NULL,
            content         TEXT NOT NULL,
            triggered_at    TEXT NOT NULL,
            suggested_inspect_time TEXT,
            priority        INTEGER NOT NULL,
            estimated_hours REAL,
            ai_measures     TEXT,
            ai_personnel    TEXT,
            ai_tools        TEXT,
            ai_materials    TEXT,
            actual_inspect_time  TEXT,
            inspect_process TEXT,
            inspect_result  TEXT,
            status          TEXT NOT NULL DEFAULT 'created',
            created_at      TEXT DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (alert_id) REFERENCES alerts(id)
        );
        CREATE TABLE IF NOT EXISTS ai_models (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            name            TEXT NOT NULL,
            component       TEXT NOT NULL,
            cycle           TEXT NOT NULL,
            file_path       TEXT NOT NULL,
            status          TEXT NOT NULL DEFAULT '已停止',
            description     TEXT,
            last_run_at     TEXT,
            created_at      TEXT DEFAULT (datetime('now','localtime')),
            updated_at      TEXT DEFAULT (datetime('now','localtime'))
        );
        CREATE INDEX IF NOT EXISTS idx_alerts_system ON alerts(system);
        CREATE INDEX IF NOT EXISTS idx_alerts_priority ON alerts(priority);
        CREATE INDEX IF NOT EXISTS idx_alerts_status ON alerts(processing_status);
        CREATE INDEX IF NOT EXISTS idx_alerts_triggered ON alerts(triggered_at);
    """)
    conn.close()


def row_to_dict(row: sqlite3.Row) -> dict:
    """Convert a Row to dict, converting is_closed/has_work_order to boolean."""
    d = dict(row)
    if "is_closed" in d:
        d["is_closed"] = bool(d["is_closed"])
    if "has_work_order" in d:
        d["has_work_order"] = bool(d["has_work_order"])
    return d
```

**关键约定**：
- `DB_PATH` 从 `.env` 读取（通过 `python-dotenv`），默认值 `./data/wind_warning.db`
- `seed.py` 和 `model_scheduler.py` 中的数据库连接也应使用 `database.py` 的 `get_db_conn()` 或 `DB_PATH`，不要硬编码路径
- `row_to_dict` 统一放在 `database.py`，各 router 导入使用

### 10.2 models.py 集中管理 Pydantic 模型

前文各 router 中 inline 定义了 `WorkOrderRequest`、`ModelUpdate`、`ToggleRequest`。统一集中到 `models.py`：

```python
# models.py

from typing import Optional
from pydantic import BaseModel


class WorkOrderRequest(BaseModel):
    alert_id: str


class ModelUpdate(BaseModel):
    name: Optional[str] = None
    component: Optional[str] = None
    cycle: Optional[str] = None
    status: Optional[str] = None
    description: Optional[str] = None


class ToggleRequest(BaseModel):
    action: str  # "start" or "stop"
```

各 router 改为 `from models import WorkOrderRequest` 等导入。

### 10.3 工单检查记录字段（本次不启用）

`work_orders` 表中的 `actual_inspect_time`、`inspect_process`、`inspect_result` 三个字段为**预留字段**，本次开发不启用（无对应接口填入）。建表时保留以备后续扩展，但 POST /api/work-orders 不写入这三列。

### 10.4 seed.py 和 model_scheduler.py 使用 DB_PATH

前文第四节 seed.py 和第七节 model_scheduler.py 中硬编码了 `sqlite3.connect("data/wind_warning.db")`。开发时应改为：

```python
from database import get_db_conn, DB_PATH

# seed.py 中
conn = get_db_conn()

# model_scheduler.py 中（调度器回调不能依赖 FastAPI 上下文，直接用 DB_PATH）
conn = sqlite3.connect(DB_PATH)
```
