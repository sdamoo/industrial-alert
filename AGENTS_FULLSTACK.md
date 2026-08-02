# AGENTS_FULLSTACK.md — 全栈 AI 编码规范（单人单机版）

> 本文件是单人同时开发前端和后端的 AI 编码规范。
> 原始的 `frontend/AGENTS.md` 和 `backend/AGENTS.md` 仍保留，供两人分工模式使用。
>
> 开发前必须完整阅读：
> 1. `API_CONTRACT.md` — 接口契约
> 2. `SPEC_FULLSTACK.md` — 全栈开发规格书

---

## 一、技术栈锁定

### 前端

- **框架**: React 18 + TypeScript
- **构建**: Vite 5
- **UI 库**: Ant Design 5（`antd@^5.20.0`）
- **图标**: `@ant-design/icons`
- **路由**: `react-router-dom@6`
- **HTTP**: axios（封装 `src/api/client.ts`，baseURL = `/api`，Mock 拦截）
- **日期**: dayjs

### 后端

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

### 前端规范

- **缩进**: 2 空格
- **引号**: 单引号 `'`
- **命名**: 变量 `camelCase`；组件 `PascalCase`
- **文件名**: `PascalCase.tsx`（组件）/ `lowercase.ts`（工具/类型）
- **语言**: 代码注释用英文；用户可见文案用中文

```typescript
// ✅ API 调用走 client.ts
import { apiClient } from '@/api/client';
const { data } = await apiClient.get<AlertListResponse>('/alerts');
const { data } = await apiClient.get<ModelListResponse>('/models');

// ✅ 类型从 types/index.ts 导入
import type { Alert, AIModel, Priority } from '@/types';

// ❌ 禁止硬编码 URL
axios.get('http://localhost:8000/api/alerts')

// ❌ 禁止内联重复类型
interface Alert { id: string; ... }
```

### 后端规范

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
    raise HTTPException(status_code=500, detail="内部错误")

# ❌ 禁止裸 except
try:
    ...
except:  # 禁止
    ...
```

---

## 三、UI 规范

### 淡蓝色主题

主题 token 集中在 `src/theme.ts`，通过 ConfigProvider 全局生效。

- 主色：`#3b82f6`
- 页面背景：`#f0f7ff`
- 禁止使用紫色/绿色/橙色作为主色调（标签除外）

### 优先级颜色编码

| 优先级 | 颜色 | Hex |
|--------|------|-----|
| 一级（紧急） | 红 | `#ef4444` |
| 二级（警告） | 橙 | `#f59e0b` |
| 三级（提示） | 蓝 | `#3b82f6` |

### 模型状态颜色编码

| 模型状态 | 颜色 | Tag color |
|----------|------|-----------|
| 运行中 | 绿 | `green` |
| 已停止 | 灰 | `default` |
| 异常 | 红 | `red` |

### 部件系统 Tag 颜色编码

| 系统 | Tag color |
|------|-----------|
| 齿轮箱系统 | `orange` |
| 发电机系统 | `blue` |
| 叶片系统 | `green` |
| 变桨系统 | `purple` |
| 偏航系统 | `cyan` |
| 液压系统 | `gold` |

### 组件规范

- **导航**: 顶部 `<TopNav>`，3 个 tab（预警信息 / 预警历史 / 模型管理），当前页高亮
- **卡片**: 左边框颜色对应优先级
- **弹窗**: AntD `Modal`，蓝边框 + 渐变标题栏
- **表格**: 状态列用 `Tag` 彩色标签
- **分页**: 默认每页 10 条
- **模型管理页**:
  - 模型列表用 `Table`，列含：名称、适用部件（Tag）、运行周期、状态（彩色 Tag）、上次运行时间、操作
  - "上传模型"按钮打开 `Modal` + `Form`，字段：名称（Input）、适用部件（Select 6 系统）、运行周期（Select: 每小时/每日/每周/每月）、描述（TextArea）、模型文件（Upload，仅 .py）
  - 每行操作按钮：启动/停止（toggle）、运行（run）、编辑（edit）、删除（Popconfirm 确认）
  - 状态 Tag 颜色严格按模型状态颜色编码表
  - 适用部件 Tag 颜色严格按部件系统颜色编码表

### 禁止事项

- ❌ 禁止 Tailwind CSS / styled-components / emotion
- ❌ 禁止引入额外 UI 库
- ❌ 禁止在页面组件内直接写 `fetch` / `axios`
- ❌ 禁止修改优先级 / 模型状态颜色编码
- ❌ 禁止上传非 .py 文件（前端 Upload accept 需限定 `.py`）

---

## 四、数据库规范

### 建表

严格使用 `SPEC_FULLSTACK.md` 第三节定义的 `alerts`、`work_orders`、`ai_models` 三张表。**禁止新增表**。

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

**ai_models 表**：
- `status`：`TEXT`（`运行中` / `已停止` / `异常`），默认 `已停止`
- `cycle`：`TEXT`（`每小时` / `每日` / `每周` / `每月`）
- `last_run_at`：`TEXT` 或 `NULL`

### 查询

- 所有 SQL 必须参数化（`?` 占位符）
- 数据库连接用上下文管理器，确保关闭

### 种子数据

运行 `python seed.py` 初始化。11 条预警 + 2 条模型 **禁止修改内容**。

---

## 五、预设建议规范

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

---

## 六、接口规范

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

### 幂等

`POST /api/work-orders` 必须幂等：同一 `alert_id` 重复调用返回已有工单，不重复创建。生成后同步更新 `alerts.has_work_order = 1`。

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
CYCLE_TRIGGER_MAP = {
    "每小时": CronTrigger(minute=0),
    "每日": CronTrigger(hour=6, minute=0),
    "每周": CronTrigger(day_of_week="mon", hour=6, minute=0),
    "每月": CronTrigger(day=1, hour=6, minute=0),
}
```

### CORS

必须配置 CORS 允许前端 `http://localhost:5173` 访问。

### 联调配置

前端 Vite proxy 已配置 `/api → http://localhost:8000`，前端 `.env` 设置 `VITE_USE_MOCK=false` 即可联调。

---

## 七、Mock 数据规范

- Mock 数据集中在 `src/api/mock/` 目录
- 11 条预警数据 **禁止修改内容**
- 2 条模型数据 **禁止修改内容**
- 预设建议模板 6 个系统 **禁止删减**
- KPI 由前端 `filter + reduce` 自动计算
- 工单生成后同步更新 `has_work_order = true`
- 模型启停 / 运行后同步更新 `status` 和 `last_run_at`
- 模型 ID 自增，新建模型初始状态为"已停止"，`last_run_at` 为 `null`

---

## 八、质量门禁

### 前端检查

- [ ] 无 TypeScript 编译错误
- [ ] 无硬编码 API 地址
- [ ] 主题颜色统一（淡蓝色 #3b82f6）
- [ ] 优先级标签颜色正确（红/橙/蓝）
- [ ] 模型状态标签颜色正确（绿/灰/红）
- [ ] 部件系统标签颜色正确（按系统映射表）
- [ ] 4 个页面路由跳转正常
- [ ] Mock 数据 11 条预警完整
- [ ] Mock 数据 2 条模型完整
- [ ] 6 个系统预设建议完整
- [ ] 模型上传仅接受 .py 文件
- [ ] 模型删除有 Popconfirm 确认
- [ ] 模型启动/停止/运行/编辑/删除操作均可正常调用 Mock 接口
- [ ] `npm run dev` 启动无报错
- [ ] Vite proxy 配置就绪（联调用）

### 后端检查

- [ ] 所有接口返回 JSON
- [ ] SQL 查询全部参数化
- [ ] `is_closed` / `has_work_order` 返回时转为 boolean
- [ ] `python seed.py` 可独立运行
- [ ] `uvicorn main:app` 启动无报错
- [ ] Swagger `/docs` 可访问
- [ ] 4 个预警接口全部可用
- [ ] 7 个模型管理接口全部可用
- [ ] POST `/api/models` 仅接受 `.py` 文件，非 `.py` 返回 400
- [ ] 上传的文件保存到 `uploads/` 目录
- [ ] APScheduler 启动时恢复 `status='运行中'` 的模型定时任务
- [ ] `toggle` 接口 `start` 添加定时任务，`stop` 移除定时任务
- [ ] `run` 接口更新 `last_run_at` 为当前时间
- [ ] `delete` 接口同时移除定时任务并删除模型文件
- [ ] 2 条种子模型数据正确
- [ ] CORS 配置正确
- [ ] 6 个系统预设建议完整

### 联调检查

- [ ] 前端 `VITE_USE_MOCK=false` 后页面正常加载
- [ ] 全部 11 个接口通过 Vite proxy 正常访问后端
- [ ] 工单生成后前端卡片状态实时更新
- [ ] 模型上传/启停/运行/删除操作前后端数据一致

---

## 九、开发顺序（单人全栈）

```
Phase 1: 后端基础（30min）
  Step 1: 项目搭建 + 建表（3 张表）+ 种子数据（12min）
  Step 2: GET /api/alerts + GET /api/alerts/:id + KPI 统计（12min）
  Step 3: 预设建议模板 + GET /api/alerts/history + POST /api/work-orders（8min）

Phase 2: 前端页面（Mock 模式，50min）
  Step 4: 项目搭建 + 导航栏 + 主题配置（8min）
  Step 5: Mock 数据 + 预设建议模板 + axios 封装（12min）
  Step 6: 页面一 预警信息页（15min）
  Step 7: 页面二 工单弹窗（12min）
  Step 8: 页面三 预警历史页（15min）
  Step 9: 页面四 模型管理页（18min）

Phase 3: 后端模型管理（25min）
  Step 10: 模型管理接口 7 个（15min）
  Step 11: APScheduler 配置 + main.py 集成（10min）

Phase 4: 联调验证（10min）
  Step 12: 前端 VITE_USE_MOCK=false，启动后端，验证全部 11 个接口
```

> **提示**：Phase 2 使用 Mock 模式，无需后端即可独立开发前端。Phase 4 联调时切换到真实后端。

---

## 十、禁止做

### 通用禁止

- ❌ 禁止调用任何外部 API
- ❌ 禁止新增第三方依赖（除 SPEC_FULLSTACK.md 列出的）
- ❌ 禁止修改种子数据内容（11 条预警 + 2 条模型）
- ❌ 禁止删减预设建议模板（6 个风电系统）
- ❌ 禁止修改接口字段名（以 API_CONTRACT.md 为准）

### 前端禁止

- ❌ 禁止引入 Tailwind / styled-components
- ❌ 禁止在页面组件内直接写 `fetch` / `axios`
- ❌ 禁止上传非 .py 模型文件

### 后端禁止

- ❌ 禁止使用 ORM（SQLAlchemy 等），直接用 `sqlite3` 标准库
- ❌ 禁止裸 `except` 吞异常
- ❌ 禁止 SQL 字符串拼接
- ❌ 禁止删除 `uploads/` 目录（运行时必须存在）
- ❌ 禁止执行上传的模型文件（`.py`）中的危险代码（如 `exec`、`eval`、`os.system` 等），定时任务回调仅模拟执行
- ❌ 禁止在 `model_scheduler.py` 中使用同步阻塞操作影响主线程

---

## 十一、遇到歧义时

1. **接口字段** → `API_CONTRACT.md`
2. **建表 SQL** → `SPEC_FULLSTACK.md` 第三节
3. **类型定义** → `SPEC_FULLSTACK.md` 第四节
4. **种子数据** → `SPEC_FULLSTACK.md` 第五节
5. **APScheduler 配置** → `SPEC_FULLSTACK.md` 第十一节
6. **主题与颜色** → `SPEC_FULLSTACK.md` 第八节
7. **组件选型** → `SPEC_FULLSTACK.md` 第九节
8. **以上都未覆盖** → 向用户提问
