# 前端开发规格书 — 风电设备预警模块

> **必读文件**（按顺序）：
> 1. `../API_CONTRACT.md` — 接口契约（字段定义、接口格式）
> 2. 本文件 — 前端类型、Mock 数据、主题配置、组件选型
> 3. `AGENTS.md` — 前端 AI 编码规范

---

## 一、项目目录结构

```
wind-warning-frontend/
├── package.json
├── vite.config.ts
├── index.html
├── .env                     # VITE_API_BASE, VITE_USE_MOCK
├── src/
│   ├── main.tsx
│   ├── App.tsx              # 路由 + ConfigProvider 主题
│   ├── theme.ts             # 淡蓝色主题 token 配置
│   ├── api/
│   │   ├── client.ts        # axios 封装 + Mock 拦截
│   │   └── mock/
│   │       ├── alerts.ts    # 预警 Mock 数据
│   │       ├── suggestions.ts # 预设建议模板
│   │       └── models.ts    # 模型管理 Mock 数据
│   ├── components/
│   │   └── TopNav.tsx       # 通用顶部导航栏
│   ├── pages/
│   │   ├── WarningInfo.tsx    # 页面一：预警信息（卡片看板）
│   │   ├── WorkOrderModal.tsx # 页面二：工单弹窗（Modal）
│   │   ├── WarningHistory.tsx # 页面三：预警历史（筛选+表格）
│   │   └── ModelManagement.tsx # 页面四：模型管理（表格+上传/编辑弹窗）
│   └── types/
│       └── index.ts         # TypeScript 类型定义
└── tsconfig.json
```

---

## 二、TypeScript 类型定义

```typescript
// src/types/index.ts

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

## 三、Mock 数据（11 条预警）

```typescript
// src/api/mock/alerts.ts

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
    content: '定子绕组温度偏高，实测118℃，限值120℃，接近预警线',
    triggered_at: '2026-07-31 14:15', suggested_inspect_time: '2026-07-31 15:00',
    priority: 2, estimated_hours: 3.0, processing_status: '处理中',
    is_closed: false, has_work_order: false, treatment_measures: '检查冷却系统流量，核实温度测点'
  },
  {
    id: 'W003', unit_id: '风机A003', system: '齿轮箱系统',
    location: '中速轴齿轮',
    content: '齿面磨损量0.8mm，预警阈值0.5mm，需评估剩余寿命',
    triggered_at: '2026-07-31 13:50', suggested_inspect_time: '2026-07-31 15:30',
    priority: 1, estimated_hours: 6.0, processing_status: '待处理',
    is_closed: false, has_work_order: false, treatment_measures: '齿面测厚复检，评估剩余寿命'
  },
  {
    id: 'W004', unit_id: '风机A003', system: '叶片系统',
    location: '1号叶片',
    content: '叶片表面裂纹检测，长度约15cm，需评估扩展风险',
    triggered_at: '2026-07-31 13:20', suggested_inspect_time: '2026-07-31 14:30',
    priority: 3, estimated_hours: 2.0, processing_status: '待处理',
    is_closed: false, has_work_order: false, treatment_measures: '无人机巡检裂纹，评估扩展风险'
  },
  {
    id: 'W005', unit_id: '风机A005', system: '变桨系统',
    location: '变桨轴承',
    content: '变桨轴承振动异常，实测7.5mm/s，限值4.5mm/s',
    triggered_at: '2026-07-31 12:40', suggested_inspect_time: '2026-07-31 14:00',
    priority: 2, estimated_hours: 3.0, processing_status: '处理中',
    is_closed: false, has_work_order: false, treatment_measures: '检查变桨轴承磨损，核实振动值'
  },
  {
    id: 'W006', unit_id: '风机A005', system: '偏航系统',
    location: '偏航轴承',
    content: '偏航轴承磨损量超限，实测间隙1.2mm，限值0.8mm',
    triggered_at: '2026-07-31 11:30', suggested_inspect_time: '2026-07-31 13:00',
    priority: 3, estimated_hours: 2.0, processing_status: '已完成',
    is_closed: true, has_work_order: false, treatment_measures: '已检查偏航轴承磨损，记录存档'
  },
  {
    id: 'W007', unit_id: '风机A007', system: '齿轮箱系统',
    location: '低速轴轴承',
    content: '润滑油压偏低，实测0.8bar，限值1.5bar',
    triggered_at: '2026-07-31 10:15', suggested_inspect_time: '2026-07-31 12:00',
    priority: 2, estimated_hours: 4.0, processing_status: '待处理',
    is_closed: false, has_work_order: false, treatment_measures: '检查润滑油压，核实管路密封'
  },
  {
    id: 'W008', unit_id: '风机A007', system: '液压系统',
    location: '液压站',
    content: '液压油温超标，实测65℃，限值55℃，持续20分钟',
    triggered_at: '2026-07-31 09:00', suggested_inspect_time: '2026-07-31 10:30',
    priority: 3, estimated_hours: 2.0, processing_status: '待处理',
    is_closed: false, has_work_order: false, treatment_measures: '检查液压油温及冷却系统'
  },
  {
    id: 'W009', unit_id: '风机A001', system: '发电机系统',
    location: '前轴承',
    content: '轴承振动超标，实测125μm，限值100μm，持续8分钟',
    triggered_at: '2026-07-31 08:45', suggested_inspect_time: '2026-07-31 10:00',
    priority: 1, estimated_hours: 3.0, processing_status: '处理中',
    is_closed: false, has_work_order: false, treatment_measures: '检查轴承振动，核实润滑状态'
  },
  {
    id: 'W010', unit_id: '风机A003', system: '叶片系统',
    location: '2号叶片',
    content: '叶片零位偏差2.5°，限值2°，需校准零位',
    triggered_at: '2026-07-30 22:30', suggested_inspect_time: '2026-07-31 08:00',
    priority: 2, estimated_hours: 2.0, processing_status: '待处理',
    is_closed: false, has_work_order: false, treatment_measures: '校准叶片零位'
  },
  {
    id: 'W011', unit_id: '风机A005', system: '变桨系统',
    location: '变桨电机',
    content: '变桨电机过热保护动作，温度92℃，限值85℃',
    triggered_at: '2026-07-30 16:00', suggested_inspect_time: '2026-07-30 18:00',
    priority: 3, estimated_hours: 1.5, processing_status: '已完成',
    is_closed: true, has_work_order: false, treatment_measures: '已检查变桨电机冷却，恢复正常'
  }
];
```

### KPI 计算逻辑

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

## 四、预设建议模板（6 个风电系统）

```typescript
// src/api/mock/suggestions.ts

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

---

## 五、Mock 模型数据（2 条）

```typescript
// src/api/mock/models.ts

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
    created_at: '2026-07-30 14:00',
    updated_at: '2026-07-30 14:00'
  }
];
```

---

## 六、Mock 拦截器

```typescript
// src/api/client.ts
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
      // 简化 Mock：返回全部数据，实际可按筛选条件过滤
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

## 七、主题配置

```typescript
// src/theme.ts
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

### 模型状态颜色编码

| 模型状态 | 颜色 | Hex / Tag color |
|----------|------|-----------------|
| 运行中 | 绿 | `#52c41a`（Tag color = `green`） |
| 已停止 | 灰 | 默认色（Tag color = `default`） |
| 异常 | 红 | `#ef4444`（Tag color = `red`） |

### 部件系统 Tag 颜色编码

| 系统 | Tag color |
|------|-----------|
| 齿轮箱系统 | `orange` |
| 发电机系统 | `blue` |
| 叶片系统 | `green` |
| 变桨系统 | `purple` |
| 偏航系统 | `cyan` |
| 液压系统 | `gold` |

---

## 八、组件选型

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

## 九、依赖与配置

### package.json

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

### .env

```env
VITE_API_BASE=/api
VITE_USE_MOCK=true
```

### vite.config.ts（联调时启用 proxy）

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

### 启动命令

```bash
npm install
npm run dev    # http://localhost:5173
```
