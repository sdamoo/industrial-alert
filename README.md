# 风电设备预警模块

> 2 人团队参赛项目 · 前后端分离 · AI 编码协同

## 快速开始

### 前端（成员 A）

```bash
cd frontend
npm install
npm run dev    # http://localhost:5173
```

Mock 模式下无需后端，数据由 `src/api/mock/` 提供。

### 后端（成员 B）

```bash
cd backend
pip install -r requirements.txt
python seed.py                                    # 初始化数据库 + 种子数据
uvicorn main:app --reload --host 0.0.0.0 --port 8000
# Swagger 文档: http://localhost:8000/docs
```

### 联调

1. 前端 `.env` 设置 `VITE_USE_MOCK=false`
2. 前端 Vite proxy 已配置 `/api → http://localhost:8000`
3. 后端 CORS 已允许 `http://localhost:5173`

## 项目结构

```
wind-warning/
├── frontend/          # 前端（React + TS + AntD 5）
├── backend/           # 后端（FastAPI + SQLite + APScheduler）
├── API_CONTRACT.md    # 接口契约
├── AGENTS.md          # AI 编码规范
└── .pre-commit-config.yaml
```

## 功能页面

| 页面 | 说明 |
|------|------|
| 预警信息看板 | KPI 统计 + 预警卡片网格 |
| 工单弹窗 | 预警详情 + 预设建议 + 生成工单 |
| 预警历史 | 多条件筛选 + 分页表格 |
| 模型管理 | 模型列表 + 上传/启停/运行/删除 |

## 部件系统

齿轮箱系统 | 发电机系统 | 叶片系统 | 变桨系统 | 偏航系统 | 液压系统

## 协作流程

1. 每人只在各自目录（`frontend/` 或 `backend/`）开发
2. 提交前运行 pre-commit（format + lint）
3. PR < 400 行，Conventional Commits 格式
4. 合并到 main 前需对方 review
5. 每天至少 push 一次备份

## 关键文件

| 文件 | 用途 |
|------|------|
| `API_CONTRACT.md` | 前后端共享接口契约 |
| `frontend/SPEC.md` | 前端开发规格书 |
| `frontend/AGENTS.md` | 前端 AI 编码规范 |
| `backend/SPEC.md` | 后端开发规格书 |
| `backend/AGENTS.md` | 后端 AI 编码规范 |
| `AGENTS.md` | 全局 AI 编码规范 |
