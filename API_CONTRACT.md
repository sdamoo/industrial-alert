# API 接口契约 — 风电设备预警模块

> **本文档是前后端共享的接口契约，前端和后端开发前都必须完整阅读。**
> 前端按此契约编写 Mock 数据和类型定义；后端按此契约实现接口返回。
> 联调时以本文档为准，任何一方不得单方面修改字段名或类型。

---

## 一、数据模型

### 1.1 Alert（预警记录）

| 字段名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `id` | string | 是 | 预警ID，如 `"W001"` |
| `unit_id` | string | 是 | 风机编号，如 `"风机A001"` |
| `system` | string | 是 | 部件系统，枚举值见 1.5 |
| `location` | string | 是 | 预警部位，如 `"高速轴轴承"` |
| `content` | string | 是 | 预警内容描述 |
| `triggered_at` | string | 是 | 预警时间，格式 `"YYYY-MM-DD HH:MM"` |
| `suggested_inspect_time` | string | 是 | 建议检查时间，格式 `"YYYY-MM-DD HH:MM"` |
| `priority` | integer | 是 | 优先级：`1`=一级(紧急) `2`=二级(警告) `3`=三级(提示) |
| `estimated_hours` | number | 是 | 预计工时（小时），如 `4.0` |
| `processing_status` | string | 是 | 处理进度：`"待处理"` `"处理中"` `"已完成"` |
| `is_closed` | boolean | 是 | 是否已关闭 |
| `has_work_order` | boolean | 是 | 是否已生成工单 |
| `treatment_measures` | string | 否 | 处理措施（历史记录用） |

### 1.2 PresetSuggestions（预设建议）

| 字段名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `measures` | string | 是 | 建议处理措施 |
| `personnel` | string | 是 | 需要人员 |
| `tools` | string | 是 | 建议检查工具 |
| `materials` | string | 是 | 建议携带物资 |

### 1.3 AlertDetail（预警详情 = Alert + 预设建议）

Alert 所有字段 + 以下字段：

| 字段名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `ai_suggestions` | PresetSuggestions | 是 | 预设建议（根据 system 字段匹配） |

### 1.4 AIModel（预警模型）

| 字段名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `id` | integer | 是 | 模型ID（自增） |
| `name` | string | 是 | 模型名称，如 `"叶片零位预警模型"` |
| `component` | string | 是 | 适用部件，枚举值同 1.5 的 system |
| `cycle` | string | 是 | 运行周期：`"每小时"` `"每日"` `"每周"` `"每月"` |
| `file_path` | string | 是 | 模型文件路径，如 `"uploads/blade_zero_model.py"` |
| `status` | string | 是 | 模型状态：`"运行中"` `"已停止"` `"异常"` |
| `description` | string | 否 | 模型描述 |
| `last_run_at` | string | 否 | 上次运行时间，格式 `"YYYY-MM-DD HH:MM"` |
| `created_at` | string | 是 | 创建时间，格式 `"YYYY-MM-DD HH:MM"` |
| `updated_at` | string | 是 | 更新时间，格式 `"YYYY-MM-DD HH:MM"` |

### 1.5 枚举值定义

**system（部件系统）**：
```
"齿轮箱系统" | "发电机系统" | "叶片系统" | "变桨系统" | "偏航系统" | "液压系统"
```

**priority（优先级）**：
```
1 = 一级（紧急）  红色 #ef4444
2 = 二级（警告）  橙色 #f59e0b
3 = 三级（提示）  蓝色 #3b82f6
```

**processing_status（处理进度）**：
```
"待处理" | "处理中" | "已完成"
```

**model_status（模型状态）**：
```
"运行中" | "已停止" | "异常"
```

**model_cycle（运行周期）**：
```
"每小时" | "每日" | "每周" | "每月"
```

---

## 二、预警接口定义

### 2.1 GET /api/alerts — 获取预警列表 + KPI 统计

**用途**：页面一加载时调用

**请求参数**：无

**响应**：

```json
{
  "alerts": [
    {
      "id": "W001",
      "unit_id": "风机A001",
      "system": "齿轮箱系统",
      "location": "高速轴轴承",
      "content": "高速轴轴承温度超标，实测85℃，限值80℃，超温5℃，持续10分钟",
      "triggered_at": "2026-07-31 14:30",
      "suggested_inspect_time": "2026-07-31 16:00",
      "priority": 1,
      "estimated_hours": 4.0,
      "processing_status": "待处理",
      "is_closed": false,
      "has_work_order": false
    }
  ],
  "kpi": {
    "齿轮箱系统": 3,
    "发电机系统": 2,
    "叶片系统": 2,
    "变桨系统": 1,
    "偏航系统": 0,
    "液压系统": 1
  },
  "total": 11
}
```

**KPI 统计逻辑**：统计 `is_closed = false` 的预警，按 `system` 分组计数。返回的 kpi 对象必须包含全部 6 个系统（值为 0 也要返回）。

---

### 2.2 GET /api/alerts/:id — 获取单条预警详情（含预设建议）

**用途**：点击卡片或表格行时调用，弹出工单弹窗

**路径参数**：`id` = 预警ID，如 `W001`

**响应**：

```json
{
  "id": "W001",
  "unit_id": "风机A001",
  "system": "齿轮箱系统",
  "location": "高速轴轴承",
  "content": "高速轴轴承温度超标，实测85℃，限值80℃，超温5℃，持续10分钟",
  "triggered_at": "2026-07-31 14:30",
  "suggested_inspect_time": "2026-07-31 16:00",
  "priority": 1,
  "estimated_hours": 4.0,
  "processing_status": "待处理",
  "is_closed": false,
  "has_work_order": false,
  "ai_suggestions": {
    "measures": "1.检查齿轮油品质及油位 2.核实轴承温度测点 3.检查冷却系统运行状态 4.必要时降功率运行",
    "personnel": "齿轮箱检修工2人、状态监测工程师1人",
    "tools": "振动分析仪、油液检测仪、红外测温仪",
    "materials": "齿轮油、密封件、备用轴承"
  }
}
```

**预设建议匹配逻辑**：根据 `system` 字段从预设建议模板中匹配。6 个系统各有对应处置方案。

**错误响应**（404）：

```json
{ "detail": "预警 ID 不存在: W999" }
```

---

### 2.3 GET /api/alerts/history — 分页查询预警历史

**用途**：页面三筛选查询

**查询参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `unit_id` | string | 否 | 风机编号筛选 |
| `system` | string | 否 | 部件系统筛选 |
| `start_time` | string | 否 | 预警时间起始 `"YYYY-MM-DD"` |
| `end_time` | string | 否 | 预警时间截止 `"YYYY-MM-DD"` |
| `status` | string | 否 | 处理进度：`待处理`/`处理中`/`已完成` |
| `priority` | integer | 否 | 优先级：`1`/`2`/`3` |
| `keyword` | string | 否 | 预警内容模糊搜索 |
| `page` | integer | 否 | 页码，默认 `1` |
| `page_size` | integer | 否 | 每页条数，默认 `10` |

**响应**：

```json
{
  "list": [
    {
      "id": "W001",
      "unit_id": "风机A001",
      "system": "齿轮箱系统",
      "location": "高速轴轴承",
      "processing_status": "待处理",
      "content": "高速轴轴承温度超标",
      "triggered_at": "2026-07-31 14:30",
      "suggested_inspect_time": "2026-07-31 16:00",
      "priority": 1,
      "estimated_hours": 4.0,
      "treatment_measures": "检查齿轮油品质"
    }
  ],
  "total": 11,
  "page": 1,
  "page_size": 10
}
```

---

### 2.4 POST /api/work-orders — 生成工单（幂等）

**用途**：页面二点击"生成工单"按钮

**请求体**：

```json
{
  "alert_id": "W001"
}
```

**幂等逻辑**：同一 `alert_id` 重复调用不重复创建，返回已有工单。

**响应（首次创建，201 Created）**：

```json
{
  "id": 1,
  "alert_id": "W001",
  "status": "created",
  "message": "工单已生成"
}
```

**响应（已存在，200 OK）**：

```json
{
  "id": 1,
  "alert_id": "W001",
  "status": "created",
  "message": "该预警已生成工单，不重复创建"
}
```

生成工单后需同步更新对应预警的 `has_work_order` 为 `true`。

---

## 三、模型管理接口定义

### 3.1 GET /api/models — 获取模型列表

**用途**：页面四（模型管理）加载时调用

**请求参数**：无

**响应**：

```json
{
  "models": [
    {
      "id": 1,
      "name": "叶片零位预警模型",
      "component": "叶片系统",
      "cycle": "每日",
      "file_path": "uploads/blade_zero_model.py",
      "status": "运行中",
      "description": "基于SCADA数据的叶片零位偏差检测模型",
      "last_run_at": "2026-07-31 06:00",
      "created_at": "2026-07-30 10:00",
      "updated_at": "2026-07-31 06:00"
    }
  ],
  "total": 1
}
```

---

### 3.2 POST /api/models — 上传新模型

**用途**：页面四点击"上传模型"按钮

**请求方式**：`multipart/form-data`

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `name` | string | 是 | 模型名称 |
| `component` | string | 是 | 适用部件（枚举值见 1.5） |
| `cycle` | string | 是 | 运行周期（枚举值见 1.5） |
| `description` | string | 否 | 模型描述 |
| `file` | file | 是 | Python 模型文件（.py） |

**响应（201 Created）**：

```json
{
  "id": 2,
  "name": "齿轮箱振动预警模型",
  "component": "齿轮箱系统",
  "cycle": "每小时",
  "file_path": "uploads/gearbox_vibration_model.py",
  "status": "已停止",
  "description": "基于振动数据的齿轮箱健康度评估模型",
  "last_run_at": null,
  "created_at": "2026-07-31 15:00",
  "updated_at": "2026-07-31 15:00"
}
```

**错误响应**（400）：

```json
{ "detail": "仅支持 .py 文件" }
```

---

### 3.3 GET /api/models/:id — 获取模型详情

**路径参数**：`id` = 模型ID

**响应**：同 3.1 中单个模型对象

**错误响应**（404）：

```json
{ "detail": "模型 ID 不存在: 999" }
```

---

### 3.4 PUT /api/models/:id — 更新模型信息

**路径参数**：`id` = 模型ID

**请求体**（JSON，所有字段可选）：

```json
{
  "name": "叶片零位预警模型V2",
  "component": "叶片系统",
  "cycle": "每小时",
  "status": "运行中",
  "description": "更新后的模型描述"
}
```

**响应**：更新后的完整模型对象

---

### 3.5 DELETE /api/models/:id — 删除模型

**路径参数**：`id` = 模型ID

**响应**：

```json
{
  "id": 2,
  "message": "模型已删除"
}
```

**错误响应**（404）：

```json
{ "detail": "模型 ID 不存在: 999" }
```

---

### 3.6 POST /api/models/:id/run — 手动运行模型

**用途**：页面四点击"运行"按钮

**路径参数**：`id` = 模型ID

**响应**：

```json
{
  "id": 1,
  "status": "运行中",
  "message": "模型已触发运行",
  "last_run_at": "2026-07-31 15:30"
}
```

---

### 3.7 POST /api/models/:id/toggle — 启停模型

**用途**：页面四点击"启动/停止"按钮

**路径参数**：`id` = 模型ID

**请求体**：

```json
{
  "action": "start"
}
```

`action` 可选值：`"start"` / `"stop"`

**响应**：

```json
{
  "id": 1,
  "status": "运行中",
  "message": "模型已启动"
}
```

---

## 四、预设建议模板（6 个系统）

前后端共用此模板。前端用于 Mock，后端用于接口返回。

| 系统 | 建议措施 | 人员 | 工具 | 物资 |
|------|---------|------|------|------|
| 齿轮箱系统 | 1.检查齿轮油品质及油位 2.核实轴承温度测点 3.检查冷却系统运行状态 4.必要时降功率运行 | 齿轮箱检修工2人、状态监测工程师1人 | 振动分析仪、油液检测仪、红外测温仪 | 齿轮油、密封件、备用轴承 |
| 发电机系统 | 1.检查冷却系统流量 2.核实温度测点 3.检查绝缘电阻 4.监测轴承振动 | 发电机检修工2人、电气工程师1人 | 兆欧表、红外热像仪、振动检测仪 | 绝缘材料、密封件、润滑油 |
| 叶片系统 | 1.目视检查叶片表面 2.使用无人机巡检裂纹 3.检查防雷装置 4.必要时停机修复 | 叶片检修工2人、无人机操作员1人 | 无人机、探伤仪、游标卡尺 | 叶片修补材料、防雷器件、密封胶 |
| 变桨系统 | 1.检查变桨轴承磨损 2.核实变桨电机温度 3.检查变桨角度传感器 4.校准变桨限位 | 变桨系统检修工2人 | 角度测量仪、振动检测仪、万用表 | 备用变桨电机、轴承、传感器 |
| 偏航系统 | 1.检查偏航轴承磨损 2.核实偏航电机电流 3.检查偏航计数器 4.润滑偏航齿圈 | 偏航系统检修工2人 | 电流钳形表、振动检测仪、润滑脂加注枪 | 润滑脂、密封件、备用偏航电机 |
| 液压系统 | 1.检查液压油温及油位 2.核实系统压力 3.检查管路接头泄漏 4.更换液压油滤芯 | 液压系统检修工2人 | 压力表、红外测温仪、泄漏检测仪 | 液压油、滤芯、密封件、管接头 |

---

## 五、字段类型对照

| 概念 | 前端（TypeScript） | 后端（Python/SQLite） | API JSON |
|------|-------------------|----------------------|----------|
| 预警ID | `string` | `str` / `TEXT` | string |
| 风机编号 | `string` | `str` / `TEXT` | string |
| 部件系统 | `SystemType` (联合类型) | `str` / `TEXT` | string |
| 优先级 | `Priority` (1\|2\|3) | `int` / `INTEGER` | number |
| 预计工时 | `number` | `float` / `REAL` | number |
| 是否关闭 | `boolean` | `int` (0/1) / `INTEGER` | boolean |
| 是否已生成工单 | `boolean` | `int` (0/1) / `INTEGER` | boolean |
| 处理进度 | `ProcessingStatus` (联合类型) | `str` / `TEXT` | string |
| 模型ID | `number` | `int` / `INTEGER` | number |
| 模型状态 | `ModelStatus` (联合类型) | `str` / `TEXT` | string |
| 运行周期 | `ModelCycle` (联合类型) | `str` / `TEXT` | string |

**关键约定**：后端 SQLite 中 `is_closed` 和 `has_work_order` 存为 `INTEGER`（0/1），**API 返回时必须转为 `boolean`**（true/false）。

---

## 六、联调配置

### 6.1 前端 Vite 代理

```typescript
// vite.config.ts
server: {
  port: 5173,
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true,
    },
  },
},
```

### 6.2 后端 CORS

```python
# main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 6.3 联调切换

前端开发时使用 Mock（`VITE_USE_MOCK=true`），联调时关闭 Mock 并配置 Vite 代理指向后端 `localhost:8000`。

---

## 七、种子数据（11 条预警）

前后端 Mock 数据 / 种子数据必须完全一致。完整数据见各自的 SPEC.md 文件，但以下关键约束双方必须遵守：

- 预警 ID 从 `W001` 到 `W011`，连续不跳号
- 覆盖全部 6 个系统
- `is_closed = true` 的预警：W006、W011
- KPI 统计结果（未关闭预警按系统分组）：
  - 齿轮箱系统: 3（W001, W003, W007）
  - 发电机系统: 2（W002, W009）
  - 叶片系统: 2（W004, W010）
  - 变桨系统: 1（W005）
  - 偏航系统: 0（W006 已关闭）
  - 液压系统: 1（W008）

---

## 八、种子模型数据（2 条）

模型管理页面的初始数据：

| ID | 名称 | 适用部件 | 运行周期 | 状态 | 描述 |
|----|------|---------|---------|------|------|
| 1 | 叶片零位预警模型 | 叶片系统 | 每日 | 运行中 | 基于SCADA数据的叶片零位偏差检测模型 |
| 2 | 齿轮箱温度预警模型 | 齿轮箱系统 | 每小时 | 已停止 | 基于温度趋势的齿轮箱健康度评估模型 |
