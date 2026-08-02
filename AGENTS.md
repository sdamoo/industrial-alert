# AGENTS.md — 风电设备预警模块 · 全局 AI 编码规范

> 本文件是所有 AI 编码工具（Trae Solo / Trae / Cursor 等）的共同规则入口。
> 前端开发者请额外阅读 `frontend/AGENTS.md`；后端开发者请额外阅读 `backend/AGENTS.md`。

---

## 一、项目概述

风电设备预警模块：4 个页面（预警信息看板、工单弹窗、预警历史、模型管理），淡蓝色风格，前后端分离。
部件系统覆盖齿轮箱、发电机、叶片、变桨、偏航、液压 6 大系统。

## 二、技术栈

| 层级 | 技术 | 版本 |
|------|------|------|
| 前端 | React + TypeScript + Vite + Ant Design 5 | React 18 / AntD 5.20 |
| 后端 | FastAPI + SQLite + Pydantic 2 + APScheduler | FastAPI 0.111 |
| HTTP | axios（前端）| - |

**禁止替换以上技术选型**，除非用户明确要求。

## 三、目录结构与分工

```
wind-warning/
├── frontend/          # 成员 A 负责（Trae Solo 开发）
│   ├── src/
│   │   ├── types/     # TypeScript 类型定义
│   │   ├── api/       # axios 封装 + Mock 拦截
│   │   ├── pages/     # 4 个页面组件
│   │   ├── components/# 通用组件
│   │   └── theme.ts   # 淡蓝色主题
│   └── AGENTS.md      # 前端 AI 编码规范
│
├── backend/           # 成员 B 负责（Trae 开发）
│   ├── routers/       # API 路由（预警 4 个 + 模型管理 7 个）
│   ├── database.py    # SQLite 连接 + 建表（3 张表）
│   ├── seed.py        # 种子数据（11 预警 + 2 模型）
│   ├── suggestions.py # 预设建议模板
│   ├── model_scheduler.py # APScheduler 定时调度
│   ├── uploads/       # 模型文件上传目录
│   └── AGENTS.md      # 后端 AI 编码规范
│
├── API_CONTRACT.md    # 前后端共享接口契约（双方必读）
├── AGENTS.md          # 本文件（全局规范）
└── .pre-commit-config.yaml
```

### 分工原则

- **成员 A**：只动 `frontend/` 目录，AI 工具启动目录锁定在 `frontend/` 内
- **成员 B**：只动 `backend/` 目录，AI 工具启动目录锁定在 `backend/` 内
- **共享文件**：`API_CONTRACT.md` 修改前需通知对方

## 四、AI 行为约束

- 禁止修改本职责目录之外的文件
- 禁止直接修改 main 分支
- 生成的代码必须能通过 pre-commit 检查
- Commit message 使用 Conventional Commits 格式（`feat:` / `fix:` / `refactor:`）
- 禁止引入 SPEC.md 未列出的第三方依赖

## 五、接口契约

所有 API 字段名、类型、响应格式以 `API_CONTRACT.md` 为准，任何一方不得单方面修改。

## 六、构建与测试

| 操作 | 前端 | 后端 |
|------|------|------|
| 安装依赖 | `npm install` | `pip install -r requirements.txt` |
| 启动开发 | `npm run dev` (port 5173) | `uvicorn main:app --reload --port 8000` |
| 初始化数据 | - | `python seed.py` |
| Lint | `npx eslint src/` | `ruff check .` |
| 构建 | `npm run build` | - |

## 七、遇到歧义时

1. **接口字段** → `API_CONTRACT.md`
2. **前端实现** → `frontend/SPEC.md`
3. **后端实现** → `backend/SPEC.md`
4. **以上都未覆盖** → 向用户提问
