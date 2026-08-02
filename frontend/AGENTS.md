# AGENTS.md — 前端 AI 编码规范

> 开发前必须完整阅读：
> 1. `../API_CONTRACT.md` — 接口契约
> 2. `SPEC.md` — 前端开发规格书

---

## 一、技术栈锁定

- **框架**: React 18 + TypeScript
- **构建**: Vite 5
- **UI 库**: Ant Design 5（`antd@^5.20.0`）
- **图标**: `@ant-design/icons`
- **路由**: `react-router-dom@6`
- **HTTP**: axios（封装 `src/api/client.ts`，baseURL = `/api`，Mock 拦截）
- **日期**: dayjs
- **数据来源**: 开发阶段用 Mock，联调阶段切真实后端

**禁止替换以上技术选型**，除非用户明确要求。

---

## 二、编码规范

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

### 组件规范

- **导航**: 顶部 `<TopNav>`，3 个 tab（预警信息 / 预警历史 / 模型管理），当前页高亮
- **卡片**: 左边框颜色对应优先级
- **弹窗**: AntD `Modal`，蓝边框 + 渐变标题栏
- **表格**: 状态列用 `Tag` 彩色标签
- **分页**: 默认每页 10 条
- **模型管理页**:
  - 模型列表用 `Table`，列含：名称、适用部件（Tag）、运行周期、状态（彩色 Tag）、上次运行时间、操作
  - "上传模型"按钮打开 `Modal` + `Form`，字段：名称（Input）、适用部件（Select 6 系统）、运行周期（Select: 每小时/每日/每周/每月）、描述（TextArea）、模型文件（Upload，仅 .py）
  - 每行操作按钮：启动/停止（toggle，根据当前状态切换文案）、运行（run）、编辑（edit，复用 Modal Form，文件字段只读）、删除（Popconfirm 确认）
  - 状态 Tag 颜色严格按上方模型状态颜色编码表
  - 适用部件 Tag 颜色严格按上方部件系统颜色编码表

### 禁止事项

- ❌ 禁止 Tailwind CSS / styled-components / emotion
- ❌ 禁止引入额外 UI 库
- ❌ 禁止在页面组件内直接写 `fetch` / `axios`
- ❌ 禁止修改优先级颜色编码
- ❌ 禁止修改模型状态颜色编码
- ❌ 禁止上传非 .py 文件（前端 Upload accept 需限定 `.py`）

---

## 四、Mock 数据规范

- Mock 数据集中在 `src/api/mock/` 目录
- 11 条预警数据 **禁止修改内容**
- 2 条模型数据 **禁止修改内容**
- 预设建议模板 6 个系统 **禁止删减**
- KPI 由前端 `filter + reduce` 自动计算
- 工单生成后同步更新 `has_work_order = true`
- 模型启停 / 运行后同步更新 `status` 和 `last_run_at`
- 模型 ID 自增，新建模型初始状态为"已停止"，`last_run_at` 为 `null`

---

## 五、质量门禁

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

---

## 六、开发顺序

```
Step 1: 项目搭建 + 导航栏 + 主题配置（8min）
Step 2: Mock 数据（11 条预警 + 2 条模型）+ 预设建议模板 + axios 封装（12min）
Step 3: 页面一 预警信息页（15min）
Step 4: 页面二 工单弹窗（12min）
Step 5: 页面三 预警历史页（15min）
Step 6: 页面四 模型管理页（表格 + 上传/编辑弹窗 + 启停/运行/删除）（18min）
Step 7: 联调验证（10min）
```

---

## 七、禁止做

- ❌ 禁止调用任何外部 API
- ❌ 禁止新增第三方依赖（除 SPEC.md 列出的）
- ❌ 禁止修改 Mock 数据内容（11 条预警 + 2 条模型）
- ❌ 禁止删减预设建议模板
- ❌ 禁止引入 Tailwind / styled-components
- ❌ 禁止修改接口字段名（以 API_CONTRACT.md 为准）
- ❌ 禁止上传非 .py 模型文件

---

## 八、遇到歧义时

1. **接口字段** → `../API_CONTRACT.md`
2. **类型定义** → `SPEC.md` 第二节
3. **Mock 数据** → `SPEC.md` 第三、五节
4. **主题与颜色** → `SPEC.md` 第七节
5. **组件选型** → `SPEC.md` 第八节
6. **以上都未覆盖** → 向用户提问
