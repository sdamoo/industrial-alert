# AGENTS.md — 后端 AI 编码规范

> 开发前必须完整阅读：
> 1. `../API_CONTRACT.md` — 接口契约
> 2. `SPEC.md` — 后端开发规格书

---

## 一、技术栈锁定

- **框架**: FastAPI 0.111
- **服务器**: uvicorn
- **数据库**: SQLite（文件存储，`./data/wind_warning.db`）
- **数据校验**: Pydantic 2
- **定时调度**: APScheduler 3.10.4（BackgroundScheduler + CronTrigger）
- **文件上传**: python-multipart 0.0.9（FastAPI UploadFile 依赖）
- **无外部 API 调用**: 预设建议为本地模板匹配，模型执行为本地模拟

**禁止替换以上技术选型**，除非用户明确要求。

---

## 二、编码规范

- **缩进**: 4 空格
- **引号**: 双引号 `"`
- **命名**: 变量 `snake_case`
- **文件名**: `snake_case.py`
- **语言**: 代码注释用英文；返回给前端的文案用中文

```python
# ✅ 路由函数有类型注解 + docstring
@router.get("/api/alerts/{alert_id}")
async def get_alert_detail(alert_id: str) -> dict:
    """获取单条预警详情，含预设建议。"""
    ...

# ✅ 参数化查询
cursor.execute("SELECT * FROM alerts WHERE id = ?", (alert_id,))

# ❌ 禁止字符串拼接 SQL
cursor.execute(f"SELECT * FROM alerts WHERE id = '{alert_id}'")

# ✅ 捕获具体异常
try:
    ...
except sqlite3.Error as e:
    logger.error(f"Database error: {e}")
    raise HTTPException(status_code=500, detail="内部错误")

# ❌ 禁止裸 except
try:
    ...
except:  # 禁止
    ...
```

---

## 三、数据库规范

### 建表

严格使用 `SPEC.md` 第二节定义的 `alerts`、`work_orders`、`ai_models` 三张表。**禁止新增表**。

### 三张表说明

| 表名 | 用途 | 主键 |
|------|------|------|
| `alerts` | 预警记录 | `id` (TEXT, 如 W001) |
| `work_orders` | 工单记录 | `id` (INTEGER, 自增) |
| `ai_models` | 预警模型管理 | `id` (INTEGER, 自增) |

### 字段约定

**alerts 表**：
- `is_closed` / `has_work_order`：SQLite 存 `INTEGER`（0/1），**API 返回转为 `boolean`**
- `priority`：`INTEGER`（1/2/3）
- `processing_status`：`TEXT`（`待处理` / `处理中` / `已完成`）
- `triggered_at` / `suggested_inspect_time`：`TEXT`，格式 `YYYY-MM-DD HH:MM`

**ai_models 表**：
- `status`：`TEXT`（`运行中` / `已停止` / `异常`），默认 `已停止`
- `cycle`：`TEXT`（`每小时` / `每日` / `每周` / `每月`）
- `last_run_at`：`TEXT` 或 `NULL`，格式 `YYYY-MM-DD HH:MM`
- `created_at` / `updated_at`：`TEXT`，默认 `datetime('now','localtime')`

### 查询

- 所有 SQL 必须参数化（`?` 占位符）
- 数据库连接用上下文管理器，确保关闭

```python
def get_db_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn
```

### 种子数据

运行 `python seed.py` 初始化。11 条预警 + 2 条模型 **禁止修改内容**。

---

## 四、预设建议规范

### 匹配逻辑

- 仅根据 `system` 字段匹配预设建议
- 6 个风电系统必须有对应模板，**禁止删减**
- 无外部 API 调用，纯本地模板匹配

### 6 个系统清单

| 系统 | 建议措施关键点 |
|------|---------------|
| 齿轮箱系统 | 检查齿轮油品质、核实轴承温度、检查冷却系统 |
| 发电机系统 | 检查冷却系统流量、核实温度测点、检查绝缘电阻 |
| 叶片系统 | 目视检查、无人机巡检、检查防雷装置 |
| 变桨系统 | 检查变桨轴承磨损、核实变桨电机温度、校准变桨限位 |
| 偏航系统 | 检查偏航轴承磨损、核实偏航电机电流、润滑偏航齿圈 |
| 液压系统 | 检查液压油温及油位、核实系统压力、更换滤芯 |

```python
from suggestions import get_suggestions

# 在 GET /api/alerts/:id 中
alert['ai_suggestions'] = get_suggestions(alert['system'])
```

---

## 五、接口规范

### 返回格式

- 所有接口返回 JSON，不裸返回字符串
- 响应字段名和类型必须与 `API_CONTRACT.md` 完全一致
- 错误返回 `{"detail": "错误信息"}` + 对应 HTTP 状态码

### 预警接口（4 个）

| 接口 | 方法 | 路径 | 要点 |
|------|------|------|------|
| 预警列表 + KPI | GET | `/api/alerts` | KPI 仅统计 `is_closed=0`，补全 6 个系统 0 值 |
| 预警详情 | GET | `/api/alerts/:id` | 404 返回 `{"detail": "预警 ID 不存在: W999"}` |
| 历史查询 | GET | `/api/alerts/history` | 支持 8 个筛选参数 + 分页 |
| 生成工单 | POST | `/api/work-orders` | 幂等：同一 alert_id 重复调用不重复创建 |

### 幂等

`POST /api/work-orders` 必须幂等：同一 `alert_id` 重复调用返回已有工单，不重复创建。生成后同步更新 `alerts.has_work_order = 1`。

### 模型管理接口（7 个）

| 接口 | 方法 | 路径 | 要点 |
|------|------|------|------|
| 模型列表 | GET | `/api/models` | 返回 `{models: [...], total: N}` |
| 上传模型 | POST | `/api/models` | `multipart/form-data`，仅允许 `.py` 文件 |
| 模型详情 | GET | `/api/models/:id` | 404 返回 `{"detail": "模型 ID 不存在: 999"}` |
| 更新模型 | PUT | `/api/models/:id` | JSON 请求体，所有字段可选 |
| 删除模型 | DELETE | `/api/models/:id` | 同时移除定时任务 + 删除文件 |
| 手动运行 | POST | `/api/models/:id/run` | 更新 `last_run_at`，返回当前时间 |
| 启停模型 | POST | `/api/models/:id/toggle` | `action` 为 `start`/`stop`，联动 APScheduler |

### 文件上传规范

```python
from fastapi import UploadFile, File, Form

# ✅ 使用 UploadFile + Form 接收 multipart/form-data
@router.post("/api/models")
async def upload_model(
    name: str = Form(...),
    component: str = Form(...),
    cycle: str = Form(...),
    description: str = Form(None),
    file: UploadFile = File(...),
) -> dict:
    # ✅ 校验文件扩展名
    if not file.filename or not file.filename.endswith(".py"):
        raise HTTPException(status_code=400, detail="仅支持 .py 文件")
    ...
```

### APScheduler 集成规范

- 调度器在 `model_scheduler.py` 中全局初始化（`BackgroundScheduler`）
- `main.py` 启动时调用 `start_scheduler()` + `restore_running_jobs()`
- `main.py` 关闭时调用 `shutdown_scheduler()`
- `toggle` 接口的 `start` 操作调用 `add_model_job()`，`stop` 操作调用 `remove_model_job()`
- `delete` 接口必须先调用 `remove_model_job()` 再删除数据库记录
- 定时任务回调函数更新 `last_run_at` 字段

```python
# ✅ 周期 → CronTrigger 映射
CYCLE_TRIGGER_MAP = {
    "每小时": CronTrigger(minute=0),
    "每日": CronTrigger(hour=6, minute=0),
    "每周": CronTrigger(day_of_week="mon", hour=6, minute=0),
    "每月": CronTrigger(day=1, hour=6, minute=0),
}
```

### CORS

必须配置 CORS 允许前端 `http://localhost:5173` 访问。

---

## 六、质量门禁

### 预警接口检查

- [ ] 所有接口返回 JSON
- [ ] SQL 查询全部参数化
- [ ] `is_closed` / `has_work_order` 返回时转为 boolean
- [ ] `python seed.py` 可独立运行
- [ ] `uvicorn main:app` 启动无报错
- [ ] Swagger `/docs` 可访问
- [ ] 4 个预警接口全部可用
- [ ] CORS 配置正确
- [ ] 6 个系统预设建议完整

### 模型管理检查

- [ ] 7 个模型管理接口全部可用
- [ ] POST `/api/models` 仅接受 `.py` 文件，非 `.py` 返回 400
- [ ] 上传的文件保存到 `uploads/` 目录
- [ ] APScheduler 启动时恢复 `status='运行中'` 的模型定时任务
- [ ] `toggle` 接口 `start` 添加定时任务，`stop` 移除定时任务
- [ ] `run` 接口更新 `last_run_at` 为当前时间
- [ ] `delete` 接口同时移除定时任务并删除模型文件
- [ ] 2 条种子模型数据正确（叶片零位预警模型=运行中，齿轮箱温度预警模型=已停止）

---

## 七、开发顺序

```
Step 1: 项目搭建 + 建表（3 张表）+ 种子数据（11 条预警 + 2 条模型）（12min）
Step 2: GET /api/alerts + GET /api/alerts/:id + KPI 统计（12min）
Step 3: 预设建议模板（6 个风电系统）+ 匹配逻辑（8min）
Step 4: GET /api/alerts/history + POST /api/work-orders（10min）
Step 5: 模型管理接口 — GET 列表 / GET 详情 / POST 上传 / PUT 更新 / DELETE 删除（15min）
Step 6: APScheduler 配置 — model_scheduler.py + 定时任务恢复（10min）
Step 7: 模型管理接口 — POST run / POST toggle + APScheduler 联动（10min）
Step 8: main.py 集成 — 挂载 models 路由 + 启动/关闭调度器 + CORS（5min）
Step 9: Swagger 验证全部 11 个接口（5min）
```

---

## 八、禁止做

- ❌ 禁止使用 ORM（SQLAlchemy 等），直接用 `sqlite3` 标准库
- ❌ 禁止调用任何外部 API
- ❌ 禁止新增第三方依赖（除 SPEC.md 列出的）
- ❌ 禁止修改种子数据内容（11 条预警 + 2 条模型）
- ❌ 禁止删减预设建议模板（6 个风电系统）
- ❌ 禁止修改接口字段名（以 API_CONTRACT.md 为准）
- ❌ 禁止裸 `except` 吞异常
- ❌ 禁止 SQL 字符串拼接
- ❌ 禁止删除 `uploads/` 目录（运行时必须存在）
- ❌ 禁止执行上传的模型文件（`.py`）中的危险代码（如 `exec`、`eval`、`os.system` 等），定时任务回调仅模拟执行
- ❌ 禁止在 `model_scheduler.py` 中使用同步阻塞操作影响主线程

---

## 九、遇到歧义时

1. **接口字段** → `../API_CONTRACT.md`
2. **建表 SQL** → `SPEC.md` 第二节
3. **种子数据** → `SPEC.md` 第四节
4. **APScheduler 配置** → `SPEC.md` 第七节
5. **以上都未覆盖** → 向用户提问
