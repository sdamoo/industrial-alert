# 全栈开发规格书 — 风电设备预警模块（单人单机版）

> **必读文件**（按顺序）：
> 1. `API_CONTRACT.md` — 接口契约（字段定义、接口格式）
> 2. 本文件 — 前端 + 后端完整规格
> 3. `AGENTS_FULLSTACK.md` — 全栈 AI 编码规范

> **适用场景**：一个人用一台电脑同时开发前端和后端。
> 原始的 `frontend/SPEC.md` 和 `backend/SPEC.md` 仍然保留，供两人分工模式使用。

---

## 一、项目整体目录结构

```
wind-warning/
├── frontend/                      # 前端项目
│   ├── package.json
│   ├── vite.config.ts
│   ├── index.html
│   ├── .env                       # VITE_API_BASE, VITE_USE_MOCK
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx                # 路由 + ConfigProvider 主题
│   │   ├── theme.ts               # 淡蓝色主题 token 配置
│   │   ├── api/
│   │   │   ├── client.ts          # axios 封装 + Mock 拦截
│   │   │   └── mock/
│   │   │       ├── alerts.ts      # 预警 Mock 数据
│   │   │       ├── suggestions.ts # 预设建议模板
│   │   │       └── models.ts      # 模型管理 Mock 数据
│   │   ├── components/
│   │   │   └── TopNav.tsx         # 通用顶部导航栏
│   │   ├── pages/
│   │   │   ├── WarningInfo.tsx      # 页面一：预警信息（卡片看板）
│   │   │   ├── WorkOrderModal.tsx   # 页面二：工单弹窗（Modal）
│   │   │   ├── WarningHistory.tsx   # 页面三：预警历史（筛选+表格）
│   │   │   └── ModelManagement.tsx  # 页面四：模型管理（表格+上传/编辑弹窗）
│   │   └── types/
│   │       └── index.ts           # TypeScript 类型定义
│   └── tsconfig.json
│
├── backend/                       # 后端项目
│   ├── main.py                    # FastAPI 入口，挂载所有路由 + CORS + APScheduler
│   ├── database.py                # SQLite 连接 + 建表（3 张表）
│   ├── models.py                  # Pydantic 数据模型
│   ├── seed.py                    # 种子数据脚本（11 alerts + 2 models）
│   ├── suggestions.py             # 预设建议模板（6 个风电系统）
│   ├── model_scheduler.py         # APScheduler 定时任务调度
│   ├── routers/
│   │   ├── alerts.py              # GET /api/alerts, GET /api/alerts/:id
│   │   ├── history.py             # GET /api/alerts/history
│   │   ├── work_orders.py         # POST /api/work-orders
│   │   └── models.py              # 模型管理 7 个接口
│   ├── uploads/                   # 模型文件上传目录
│   ├── data/                      # SQLite 文件目录（运行时生成）
│   ├── requirements.txt
│   └── .env
│
├── API_CONTRACT.md                # 前后端共享接口契约
├── AGENTS_FULLSTACK.md            # 全栈 AI 编码规范（本模式使用）
└── .pre-commit-config.yaml
```

---

## 二、开发环境准备（单机）

### 2.1 需要安装的软件

| 软件 | 用途 | 版本要求 |
|------|------|---------|
| Node.js | 前端构建 | 20+ |
| Python | 后端运行 | 3.10+ |
| Git | 版本控制 | 任意 |

### 2.2 一键初始化

```bash
# 后端
cd backend
pip install -r requirements.txt
python seed.py                              # 初始化数据库 + 种子数据

# 前端
cd ../frontend
npm install
```

### 2.3 日常开发启动（两个终端）

**终端 1 — 后端**：
```bash
cd backend
uvicorn main:app --reload --port 8000
# Swagger 文档: http://localhost:8000/docs
```

**终端 2 — 前端**：
```bash
cd frontend
npm run dev
# http://localhost:5173
```

### 2.4 Mock 模式 vs 联调模式

前端 `.env` 文件控制：

```env
# Mock 模式（无需后端，数据由前端 Mock 提供）
VITE_API_BASE=/api
VITE_USE_MOCK=true

# 联调模式（需要后端运行，Vite proxy 自动转发）
VITE_API_BASE=/api
VITE_USE_MOCK=false
```

**建议开发顺序**：先用 Mock 模式开发完前端页面，再切联调模式验证后端接口。

---

## 三、数据库表结构（SQLite）

### 3.1 alerts 表

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

### 3.2 work_orders 表

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

### 3.3 ai_models 表

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

### 3.4 字段转换约定

SQLite 中 `is_closed` 和 `has_work_order` 存为 `INTEGER`（0/1），**API 返回时必须转为 `boolean`**：

```python
def row_to_dict(row):
    d = dict(row)
    d['is_closed'] = bool(d['is_closed'])
    d['has_work_order'] = bool(d['has_work_order'])
    return d
```

---

## 四、TypeScript 类型定义

```typescript
// frontend/src/types/index.ts

export type SystemType = '齿轮箱系统' | '发电机系统' | '叶片系统' | '变桨系统' | '偏航系统' | '液压系统';
export type Priority = 1 | 2 | 3;
export type ProcessingStatus = '待处理' | '处理中' | '已完成';
export type ModelStatus = '运行中' | '已停止' | '异常';
export type ModelCycle = '每小时' | '每日' | '每周' | '每月';

export interface Alert {
  id: string;
  unit_id: string;
  system: SystemType;
  location: string;
  content: string;
  triggered_at: string;
  suggested_inspect_time: string;
  priority: Priority;
  estimated_hours: number;
  processing_status: ProcessingStatus;
  is_closed: boolean;
  has_work_order: boolean;
  treatment_measures?: string;
}

export interface AlertListResponse {
  alerts: Alert[];
  kpi: Record<SystemType, number>;
  total: number;
}

export interface PresetSuggestions {
  measures: string;
  personnel: string;
  tools: string;
  materials: string;
}

export interface AlertDetail extends Alert {
  ai_suggestions: PresetSuggestions;
}

export interface HistoryQuery {
  unit_id?: string;
  system?: string;
  start_time?: string;
  end_time?: string;
  status?: ProcessingStatus;
  priority?: Priority;
  keyword?: string;
  page?: number;
  page_size?: number;
}

export interface HistoryResponse {
  list: Alert[];
  total: number;
  page: number;
  page_size: number;
}

export interface WorkOrderRequest {
  alert_id: string;
}

export interface WorkOrderResponse {
  id: number;
  alert_id: string;
  status: string;
  message: string;
}

// ---- 模型管理相关类型 ----

export interface AIModel {
  id: number;
  name: string;
  component: SystemType;
  cycle: ModelCycle;
  file_path: string;
  status: ModelStatus;
  description?: string;
  last_run_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ModelListResponse {
  models: AIModel[];
  total: number;
}

export interface ModelUploadRequest {
  name: string;
  component: SystemType;
  cycle: ModelCycle;
  description?: string;
  file: File;
}

export interface ModelUpdateRequest {
  name?: string;
  component?: SystemType;
  cycle?: ModelCycle;
  status?: ModelStatus;
  description?: string;
}

export interface ModelToggleRequest {
  action: 'start' | 'stop';
}

export interface ModelToggleResponse {
  id: number;
  status: ModelStatus;
  message: string;
}

export interface ModelRunResponse {
  id: number;
  status: ModelStatus;
  message: string;
  last_run_at: string;
}

export interface ModelDeleteResponse {
  id: number;
  message: string;
}
```

---

## 五、种子数据（11 条预警 + 2 条模型）

### 5.1 前端 Mock 数据（TypeScript）

```typescript
// frontend/src/api/mock/alerts.ts

import type { Alert } from '@/types';

export const mockAlerts: Alert[] = [
  {
    id: 'W001', unit_id: '风机A001', system: '齿轮箱系统',
    location: '高速轴轴承',
    content: '高速轴轴承温度超标，实测85℃，限值80℃，超温5℃，持续10分钟',
    triggered_at: '2026-07-31 14:30', suggested_inspect_time: '2026-07-31 16:00',
    priority: 1, estimated_hours: 4.0, processing_status: '待处理',
    is_closed: false, has_work_order: false, treatment_measures: '检查齿轮油品质及油位，核实轴承温度测点'
  },
  {
    id: 'W002', unit_id: '风机A001', system: '发电机系统',
    location: '定子绕组',
    content: '定子绕组温度偏高，实测118℃，限值120℃，接近预警线，持续8分钟',
    triggered_at: '2026-07-31 14:15', suggested_inspect_time: '2026-07-31 15:30',
    priority: 3, estimated_hours: 1.5, processing_status: '待处理',
    is_closed: false, has_work_order: false, treatment_measures: '检查冷却系统流量，核实温度测点'
  },
  {
    id: 'W003', unit_id: '风机A003', system: '齿轮箱系统',
    location: '中速轴齿轮',
    content: '中速轴齿轮齿面磨损预警，振动特征频率异常，磨损量0.6mm，阈值0.5mm',
    triggered_at: '2026-07-31 13:50', suggested_inspect_time: '2026-07-31 15:00',
    priority: 2, estimated_hours: 5.0, processing_status: '待处理',
    is_closed: false, has_work_order: false, treatment_measures: '检查齿轮啮合状态，评估齿面磨损'
  },
  {
    id: 'W004', unit_id: '风机A003', system: '叶片系统',
    location: '1号叶片',
    content: '1号叶片表面裂纹检测，发现长约15cm裂纹，位于叶片前缘，需评估扩展风险',
    triggered_at: '2026-07-31 13:20', suggested_inspect_time: '2026-07-31 14:30',
    priority: 2, estimated_hours: 6.0, processing_status: '待处理',
    is_closed: false, has_work_order: false, treatment_measures: '目视检查叶片表面，使用无人机巡检裂纹'
  },
  {
    id: 'W005', unit_id: '风机A005', system: '变桨系统',
    location: '变桨轴承',
    content: '变桨轴承振动异常，实测7.5mm/s，限值4.5mm/s，持续12分钟',
    triggered_at: '2026-07-31 12:40', suggested_inspect_time: '2026-07-31 14:00',
    priority: 1, estimated_hours: 4.0, processing_status: '待处理',
    is_closed: false, has_work_order: false, treatment_measures: '检查变桨轴承磨损，核实振动测点'
  },
  {
    id: 'W006', unit_id: '风机A005', system: '偏航系统',
    location: '偏航轴承',
    content: '偏航轴承磨损量超限，实测1.2mm，预警阈值1.0mm，需检查润滑',
    triggered_at: '2026-07-31 11:30', suggested_inspect_time: '2026-07-31 13:00',
    priority: 3, estimated_hours: 2.0, processing_status: '已完成',
    is_closed: true, has_work_order: false, treatment_measures: '已检查偏航轴承磨损，润滑后恢复正常'
  },
  {
    id: 'W007', unit_id: '风机A007', system: '齿轮箱系统',
    location: '低速轴轴承',
    content: '低速轴轴承润滑油压偏低，实测1.2bar，正常值2.0bar，需检查供油系统',
    triggered_at: '2026-07-31 10:15', suggested_inspect_time: '2026-07-31 12:00',
    priority: 2, estimated_hours: 3.0, processing_status: '待处理',
    is_closed: false, has_work_order: false, treatment_measures: '检查供油系统，核实油压测点'
  },
  {
    id: 'W008', unit_id: '风机A007', system: '液压系统',
    location: '液压站',
    content: '液压站油温超标，实测65℃，限值55℃，超温10℃，持续15分钟',
    triggered_at: '2026-07-31 09:00', suggested_inspect_time: '2026-07-31 10:30',
    priority: 1, estimated_hours: 3.0, processing_status: '待处理',
    is_closed: false, has_work_order: false, treatment_measures: '检查液压油温及冷却系统，更换滤芯'
  },
  {
    id: 'W009', unit_id: '风机A001', system: '发电机系统',
    location: '前轴承',
    content: '发电机前轴承振动超标，实测125μm，限值100μm，持续8分钟',
    triggered_at: '2026-07-31 08:45', suggested_inspect_time: '2026-07-31 10:00',
    priority: 2, estimated_hours: 3.0, processing_status: '处理中',
    is_closed: false, has_work_order: false, treatment_measures: '检查轴承间隙，核实振动测点'
  },
  {
    id: 'W010', unit_id: '风机A003', system: '叶片系统',
    location: '2号叶片',
    content: '2号叶片零位偏差2.5°，限值2°，需校准变桨零位',
    triggered_at: '2026-07-30 22:30', suggested_inspect_time: '2026-07-31 08:00',
    priority: 3, estimated_hours: 2.0, processing_status: '待处理',
    is_closed: false, has_work_order: false, treatment_measures: '校准变桨零位，检查角度传感器'
  },
  {
    id: 'W011', unit_id: '风机A005', system: '变桨系统',
    location: '变桨电机',
    content: '变桨电机过热保护动作，电机温度92℃，限值85℃，已自动停机',
    triggered_at: '2026-07-30 16:00', suggested_inspect_time: '2026-07-30 18:00',
    priority: 3, estimated_hours: 2.0, processing_status: '已完成',
    is_closed: true, has_work_order: false, treatment_measures: '已检查变桨电机散热，更换冷却风扇'
  }
];
```

### 5.2 后端种子数据（Python）

```python
# backend/seed.py

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

### 5.3 前端 Mock 模型数据

```typescript
// frontend/src/api/mock/models.ts

import type { AIModel } from '@/types';

export const mockModels: AIModel[] = [
  {
    id: 1,
    name: '叶片零位预警模型',
    component: '叶片系统',
    cycle: '每日',
    file_path: 'uploads/blade_zero_model.py',
    status: '运行中',
    description: '基于SCADA数据的叶片零位偏差检测模型',
    last_run_at: '2026-07-31 06:00',
    created_at: '2026-07-30 10:00',
    updated_at: '2026-07-31 06:00'
  },
  {
    id: 2,
    name: '齿轮箱温度预警模型',
    component: '齿轮箱系统',
    cycle: '每小时',
    file_path: 'uploads/gearbox_temp_model.py',
    status: '已停止',
    description: '基于温度趋势的齿轮箱健康度评估模型',
    last_run_at: null,
    created_at: '2026-07-28 09:00',
    updated_at: '2026-07-30 14:00'
  }
];
```

### 5.4 KPI 计算逻辑

```typescript
const kpi = mockAlerts
  .filter(a => !a.is_closed)
  .reduce((acc, a) => {
    acc[a.system] = (acc[a.system] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);
// 预期：齿轮箱3, 发电机2, 叶片2, 变桨1, 偏航0, 液压1
```

---

## 六、预设建议模板（6 个风电系统）

### 6.1 前端 TypeScript 版

```typescript
// frontend/src/api/mock/suggestions.ts

import type { PresetSuggestions } from '@/types';

export const PRESET_SUGGESTIONS: Record<string, PresetSuggestions> = {
  '齿轮箱系统': {
    measures: '1.检查齿轮油品质及油位 2.核实轴承温度测点 3.检查冷却系统运行状态 4.必要时降功率运行',
    personnel: '齿轮箱检修工2人、状态监测工程师1人',
    tools: '振动分析仪、油液检测仪、红外测温仪',
    materials: '齿轮油、密封件、备用轴承'
  },
  '发电机系统': {
    measures: '1.检查冷却系统流量 2.核实温度测点 3.检查绝缘电阻 4.监测轴承振动',
    personnel: '发电机检修工2人、电气工程师1人',
    tools: '兆欧表、红外热像仪、振动检测仪',
    materials: '绝缘材料、密封件、润滑油'
  },
  '叶片系统': {
    measures: '1.目视检查叶片表面 2.使用无人机巡检裂纹 3.检查防雷装置 4.必要时停机修复',
    personnel: '叶片检修工2人、无人机操作员1人',
    tools: '无人机、探伤仪、游标卡尺',
    materials: '叶片修补材料、防雷器件、密封胶'
  },
  '变桨系统': {
    measures: '1.检查变桨轴承磨损 2.核实变桨电机温度 3.检查变桨角度传感器 4.校准变桨限位',
    personnel: '变桨系统检修工2人',
    tools: '角度测量仪、振动检测仪、万用表',
    materials: '备用变桨电机、轴承、传感器'
  },
  '偏航系统': {
    measures: '1.检查偏航轴承磨损 2.核实偏航电机电流 3.检查偏航计数器 4.润滑偏航齿圈',
    personnel: '偏航系统检修工2人',
    tools: '电流钳形表、振动检测仪、润滑脂加注枪',
    materials: '润滑脂、密封件、备用偏航电机'
  },
  '液压系统': {
    measures: '1.检查液压油温及油位 2.核实系统压力 3.检查管路接头泄漏 4.更换液压油滤芯',
    personnel: '液压系统检修工2人',
    tools: '压力表、红外测温仪、泄漏检测仪',
    materials: '液压油、滤芯、密封件、管接头'
  }
};
```

### 6.2 后端 Python 版

```python
# backend/suggestions.py

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

## 七、前端 Mock 拦截器

```typescript
// frontend/src/api/client.ts
import axios from 'axios';
import { mockAlerts } from './mock/alerts';
import { PRESET_SUGGESTIONS } from './mock/suggestions';
import { mockModels } from './mock/models';
import type {
  AlertListResponse,
  AlertDetail,
  HistoryResponse,
  AIModel,
} from '@/types';

const apiClient = axios.create({ baseURL: '/api' });
const USE_MOCK = import.meta.env.VITE_USE_MOCK === 'true';

// 模型自增 ID 计数器
let modelIdSeq = mockModels.length;

if (USE_MOCK) {
  apiClient.interceptors.request.use(async (config) => {
    const url = config.url || '';
    const method = (config.method || 'get').toLowerCase();

    // ===== 预警相关接口 =====

    // GET /api/alerts
    if (url === '/alerts' && method === 'get') {
      const kpi = mockAlerts.filter(a => !a.is_closed).reduce((acc, a) => {
        acc[a.system] = (acc[a.system] || 0) + 1;
        return acc;
      }, {} as Record<string, number>);
      return Promise.reject({ __MOCK__: true, data: { alerts: mockAlerts, kpi, total: mockAlerts.length } });
    }

    // GET /api/alerts/:id
    if (url.match(/^\/alerts\/[^/]+$/) && method === 'get') {
      const id = url.split('/')[2];
      const alert = mockAlerts.find(a => a.id === id);
      if (!alert) return Promise.reject({ __MOCK__: true, status: 404, data: { detail: `预警 ID 不存在: ${id}` } });
      const detail = { ...alert, ai_suggestions: PRESET_SUGGESTIONS[alert.system] };
      return Promise.reject({ __MOCK__: true, data: detail });
    }

    // GET /api/alerts/history
    if (url.includes('/alerts/history') && method === 'get') {
      return Promise.reject({ __MOCK__: true, data: { list: mockAlerts, total: mockAlerts.length, page: 1, page_size: 10 } });
    }

    // POST /api/work-orders
    if (url === '/work-orders' && method === 'post') {
      const alertId = config.data?.alert_id;
      const alert = mockAlerts.find(a => a.id === alertId);
      if (alert?.has_work_order) {
        return Promise.reject({ __MOCK__: true, status: 200, data: { id: 1, alert_id: alertId, status: 'created', message: '该预警已生成工单，不重复创建' } });
      }
      if (alert) alert.has_work_order = true;
      return Promise.reject({ __MOCK__: true, status: 201, data: { id: 1, alert_id: alertId, status: 'created', message: '工单已生成' } });
    }

    // ===== 模型管理相关接口 =====

    // GET /api/models
    if (url === '/models' && method === 'get') {
      return Promise.reject({ __MOCK__: true, data: { models: mockModels, total: mockModels.length } });
    }

    // POST /api/models （上传新模型，multipart/form-data）
    if (url === '/models' && method === 'post') {
      const formData = config.data as FormData;
      const name = formData?.get('name') as string;
      const component = formData?.get('component') as string;
      const cycle = formData?.get('cycle') as string;
      const description = (formData?.get('description') as string) || '';
      const file = formData?.get('file') as File;
      if (file && !file.name.endsWith('.py')) {
        return Promise.reject({ __MOCK__: true, status: 400, data: { detail: '仅支持 .py 文件' } });
      }
      const now = '2026-07-31 15:00';
      const newModel: AIModel = {
        id: ++modelIdSeq,
        name,
        component: component as AIModel['component'],
        cycle: cycle as AIModel['cycle'],
        file_path: `uploads/${file?.name || 'model.py'}`,
        status: '已停止',
        description,
        last_run_at: null,
        created_at: now,
        updated_at: now,
      };
      mockModels.push(newModel);
      return Promise.reject({ __MOCK__: true, status: 201, data: newModel });
    }

    // GET /api/models/:id
    if (url.match(/^\/models\/[^/]+$/) && method === 'get') {
      const id = Number(url.split('/')[2]);
      const model = mockModels.find(m => m.id === id);
      if (!model) return Promise.reject({ __MOCK__: true, status: 404, data: { detail: `模型 ID 不存在: ${id}` } });
      return Promise.reject({ __MOCK__: true, data: model });
    }

    // PUT /api/models/:id
    if (url.match(/^\/models\/[^/]+$/) && method === 'put') {
      const id = Number(url.split('/')[2]);
      const model = mockModels.find(m => m.id === id);
      if (!model) return Promise.reject({ __MOCK__: true, status: 404, data: { detail: `模型 ID 不存在: ${id}` } });
      const body = typeof config.data === 'string' ? JSON.parse(config.data) : config.data;
      Object.assign(model, body, { updated_at: '2026-07-31 15:30' });
      return Promise.reject({ __MOCK__: true, data: model });
    }

    // DELETE /api/models/:id
    if (url.match(/^\/models\/[^/]+$/) && method === 'delete') {
      const id = Number(url.split('/')[2]);
      const idx = mockModels.findIndex(m => m.id === id);
      if (idx === -1) return Promise.reject({ __MOCK__: true, status: 404, data: { detail: `模型 ID 不存在: ${id}` } });
      mockModels.splice(idx, 1);
      return Promise.reject({ __MOCK__: true, data: { id, message: '模型已删除' } });
    }

    // POST /api/models/:id/run （手动运行模型）
    if (url.match(/^\/models\/[^/]+\/run$/) && method === 'post') {
      const id = Number(url.split('/')[2]);
      const model = mockModels.find(m => m.id === id);
      if (!model) return Promise.reject({ __MOCK__: true, status: 404, data: { detail: `模型 ID 不存在: ${id}` } });
      const now = '2026-07-31 15:30';
      model.last_run_at = now;
      model.updated_at = now;
      return Promise.reject({ __MOCK__: true, data: { id, status: '运行中', message: '模型已触发运行', last_run_at: now } });
    }

    // POST /api/models/:id/toggle （启停模型）
    if (url.match(/^\/models\/[^/]+\/toggle$/) && method === 'post') {
      const id = Number(url.split('/')[2]);
      const model = mockModels.find(m => m.id === id);
      if (!model) return Promise.reject({ __MOCK__: true, status: 404, data: { detail: `模型 ID 不存在: ${id}` } });
      const body = typeof config.data === 'string' ? JSON.parse(config.data) : config.data;
      const action = body?.action;
      model.status = action === 'start' ? '运行中' : '已停止';
      model.updated_at = '2026-07-31 15:30';
      const msg = action === 'start' ? '模型已启动' : '模型已停止';
      return Promise.reject({ __MOCK__: true, data: { id, status: model.status, message: msg } });
    }

    return config;
  });

  // 拦截 Mock 响应
  apiClient.interceptors.response.use(
    (response) => response,
    (error) => {
      if (error.__MOCK__) {
        return Promise.resolve({ data: error.data, status: error.status || 200 });
      }
      return Promise.reject(error);
    }
  );
}

export { apiClient };
```

---

## 八、前端主题配置

```typescript
// frontend/src/theme.ts
import type { ThemeConfig } from 'antd';

export const theme: ThemeConfig = {
  token: {
    colorPrimary: '#3b82f6',
    colorBgLayout: '#f0f7ff',
    colorBgContainer: '#ffffff',
    colorBorder: '#d6e8ff',
    colorText: '#1e3a5f',
    colorTextSecondary: '#64748b',
    borderRadius: 8,
    fontSize: 14,
  },
  components: {
    Table: {
      headerBg: '#dbeafe',
      headerColor: '#1e3a5f',
      rowHoverBg: '#eff6ff',
    },
    Modal: {
      headerBg: 'linear-gradient(90deg,#3b82f6,#0ea5e9)',
    },
  },
};
```

### 颜色编码表

**优先级颜色**：

| 优先级 | 颜色 | Hex |
|--------|------|-----|
| 一级（紧急） | 红 | `#ef4444` |
| 二级（警告） | 橙 | `#f59e0b` |
| 三级（提示） | 蓝 | `#3b82f6` |

**模型状态颜色**：

| 模型状态 | Tag color |
|----------|-----------|
| 运行中 | `green` |
| 已停止 | `default` |
| 异常 | `red` |

**部件系统 Tag 颜色**：

| 系统 | Tag color |
|------|-----------|
| 齿轮箱系统 | `orange` |
| 发电机系统 | `blue` |
| 叶片系统 | `green` |
| 变桨系统 | `purple` |
| 偏航系统 | `cyan` |
| 液压系统 | `gold` |

---

## 九、前端组件选型

| 页面 | UI 区域 | AntD 组件 | 关键属性 |
|------|---------|-----------|---------|
| 页面一 | KPI 圆环 | `Progress type="circle"` | strokeColor 按级别动态着色 |
| 页面一 | 预警卡片 | `Card` + `Tag` + `Badge` | Badge.Ribbon 做角标颜色 |
| 页面一 | 卡片网格 | `Row` + `Col span={6}` | 4 列 × 2 行 |
| 页面二 | 工单弹窗 | `Modal` + `Descriptions` | bordered, column={2} |
| 页面二 | 底部按钮 | `Button` | type="default" / type="primary" |
| 页面三 | 筛选栏 | `Form` + `Select` + `DatePicker.RangePicker` | layout="inline" |
| 页面三 | 数据表格 | `Table` + `Tag` + `Pagination` | scroll={{x:1200}} |
| 页面四 | 模型列表 | `Table` + `Tag` + `Button` | 状态列彩色 Tag，操作列按钮组 |
| 页面四 | 上传/编辑弹窗 | `Modal` + `Form` + `Input` + `Select` + `Upload` + `Input.TextArea` | file 仅接受 .py |
| 页面四 | 删除确认 | `Popconfirm` | danger，title="确定删除该模型？" |
| 页面四 | 部件系统列 | `Tag` | color 按系统映射 |
| 页面四 | 模型状态列 | `Tag` | color 按状态映射 |

---

## 十、后端接口实现要点

### 10.1 GET /api/alerts

```python
# backend/routers/alerts.py

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

### 10.2 GET /api/alerts/:id

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
    alert['ai_suggestions'] = get_suggestions(alert['system'])
    conn.close()
    return alert
```

### 10.3 GET /api/alerts/history

```python
# backend/routers/history.py

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

### 10.4 POST /api/work-orders

```python
# backend/routers/work_orders.py

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

### 10.5 模型管理接口（7 个）

```python
# backend/routers/models.py

import os
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from database import get_db_conn
from model_scheduler import add_model_job, remove_model_job
from datetime import datetime

router = APIRouter()


def model_row_to_dict(row):
    return dict(row)


@router.get("/api/models")
async def get_models() -> dict:
    """获取模型列表。"""
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
    description: str = Form(None),
    file: UploadFile = File(...),
) -> dict:
    """上传新模型文件并创建记录。仅支持 .py 文件。"""
    if not file.filename or not file.filename.endswith(".py"):
        raise HTTPException(status_code=400, detail="仅支持 .py 文件")

    os.makedirs("uploads", exist_ok=True)
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


@router.delete("/api/models/{model_id}")
async def delete_model(model_id: int) -> dict:
    """删除模型记录，同时移除定时任务并删除文件。"""
    conn = get_db_conn()
    row = conn.execute("SELECT * FROM ai_models WHERE id = ?", (model_id,)).fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail=f"模型 ID 不存在: {model_id}")

    file_path = row['file_path']
    remove_model_job(model_id)

    conn.execute("DELETE FROM ai_models WHERE id = ?", (model_id,))
    conn.commit()
    conn.close()

    if file_path and os.path.exists(file_path):
        os.remove(file_path)

    return {"id": model_id, "message": "模型已删除"}


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
        add_model_job(model_id, row['cycle'], row['file_path'])
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
        raise HTTPException(status_code=400, detail="action 仅支持 'start' 或 'stop'")

    conn.commit()
    conn.close()

    return {"id": model_id, "status": status, "message": message}
```

---

## 十一、APScheduler 配置

```python
# backend/model_scheduler.py

import sqlite3
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

scheduler = BackgroundScheduler()

CYCLE_TRIGGER_MAP = {
    "每小时": CronTrigger(minute=0),
    "每日": CronTrigger(hour=6, minute=0),
    "每周": CronTrigger(day_of_week="mon", hour=6, minute=0),
    "每月": CronTrigger(day=1, hour=6, minute=0),
}


def run_model_job(model_id: int, file_path: str):
    """定时任务回调函数：执行模型并更新 last_run_at。"""
    try:
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
    trigger = CYCLE_TRIGGER_MAP.get(cycle)
    if trigger is None:
        return
    remove_model_job(model_id)
    job_id = f"model_{model_id}"
    scheduler.add_job(
        run_model_job, trigger=trigger, args=[model_id, file_path],
        id=job_id, replace_existing=True,
    )


def remove_model_job(model_id: int):
    job_id = f"model_{model_id}"
    try:
        scheduler.remove_job(job_id)
    except Exception:
        pass


def restore_running_jobs():
    conn = sqlite3.connect("data/wind_warning.db")
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT id, cycle, file_path FROM ai_models WHERE status = '运行中'"
    ).fetchall()
    conn.close()
    for row in rows:
        add_model_job(row['id'], row['cycle'], row['file_path'])


def start_scheduler():
    if not scheduler.running:
        scheduler.start()


def shutdown_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)
```

---

## 十二、main.py 入口

```python
# backend/main.py

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

app.include_router(alerts.router)
app.include_router(history.router)
app.include_router(work_orders.router)
app.include_router(models.router)


@app.on_event("startup")
async def startup():
    os.makedirs("data", exist_ok=True)
    os.makedirs("uploads", exist_ok=True)
    init_db()
    start_scheduler()
    restore_running_jobs()


@app.on_event("shutdown")
async def shutdown():
    shutdown_scheduler()


@app.get("/")
async def root() -> dict:
    return {"message": "风电设备预警模块 API", "docs": "/docs"}
```

---

## 十三、环境配置

### 13.1 前端 package.json

```json
{
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "react-router-dom": "^6.24.0",
    "antd": "^5.20.0",
    "@ant-design/icons": "^5.3.0",
    "axios": "^1.7.2",
    "dayjs": "^1.11.11"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.3.0",
    "typescript": "^5.5.0",
    "vite": "^5.3.0"
  }
}
```

### 13.2 前端 .env

```env
VITE_API_BASE=/api
VITE_USE_MOCK=true
```

### 13.3 前端 vite.config.ts

```typescript
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
});
```

### 13.4 后端 .env

```env
DB_PATH=./data/wind_warning.db
HOST=0.0.0.0
PORT=8000
```

### 13.5 后端 requirements.txt

```
fastapi==0.111.0
uvicorn[standard]==0.30.1
pydantic==2.7.1
python-dotenv==1.0.1
apscheduler==3.10.4
python-multipart==0.0.9
```

---

## 十四、全栈开发顺序（单人）

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
