# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

KiroHub 是一个 Docker Compose 单体仓库，专注于 Kiro 账号管理：
- **KiroHub/** — Next.js 16 前端 (TypeScript, React 19, Tailwind CSS 4)
- **KiroHub-Backend/** — FastAPI 后端 (Python 3.10+, SQLAlchemy 2.0, Alembic)

## 常用命令

### Docker 部署（推荐）
```bash
cp .env.example .env
docker compose up -d

# 生成加密密钥
docker compose run --rm backend python generate_encryption_key.py
```

### 模块本地开发

**前端 (KiroHub/)**
```bash
cd KiroHub && pnpm install
pnpm dev      # 开发服务器
pnpm build    # 构建
pnpm lint     # ESLint 检查
```

**后端 (KiroHub-Backend/)**
```bash
cd KiroHub-Backend && uv sync
uv run uvicorn app.main:app --reload --port 8000

# 数据库迁移
uv run alembic upgrade head
uv run alembic revision --autogenerate -m "描述"
uv run alembic downgrade -1
```

## 架构说明

### 支持的 Kiro 账号类型
| 类型 | 说明 |
|------|------|
| AWS-IMA (Builder ID / AWS IdC) | 通过 AWS Identity Center 认证 |
| 企业账户（Enterprise） | 批量导入企业账号 |

### 后端架构 (FastAPI)
```
app/
├── api/routes/     # 路由端点（auth, kiro, kiro_aws_idc, kiro_enterprise, v1 等）
├── core/           # 配置(config.py)、安全(security.py)、异常
├── db/             # SQLAlchemy 会话管理
├── models/         # ORM 模型
├── repositories/   # 数据仓储层
├── schemas/        # Pydantic 模型
├── services/       # 业务逻辑层（kiro_service.py）
└── utils/          # 工具函数（加密、转换器等）
```

### 前端架构 (Next.js App Router)
```
app/
├── api/            # API 路由
├── auth/           # 认证页面
├── backend/        # 后端代理路由
└── dashboard/      # 仪表盘页面
```

## 代码规范

- **TypeScript**: 组件用 PascalCase，变量/函数用 camelCase；运行 `pnpm lint` 检查
- **Python**: 4 空格缩进，异步路由保持非阻塞，类型注解
- **提交信息**: `<type>: <summary>`（feat:, fix:, !表示破坏性变更）
- **模块独立性**: 保持改动范围在所修改的模块内，遵循该文件夹的现有模式

## 生成的工件

以下文件不应该被提交（各模块的 `.gitignore` 已配置）：
- `.next/` — Next.js 构建输出
- `node_modules/` — npm 依赖
- `.venv/` — Python 虚拟环境
- `__pycache__/` — Python 缓存

## 环境变量

必须配置的密钥（在 `.env` 中）：
- `JWT_SECRET_KEY` — JWT 签名密钥
- `PLUGIN_API_ENCRYPTION_KEY` — Fernet 加密密钥（32字节 base64）

可选配置：
- `ADMIN_USERNAME` / `ADMIN_PASSWORD` — 首次启动自动创建管理员
- `KIRO_PROXY_URL` — Kiro 出站代理

**添加新环境变量时**，需要同时更新对应的 `*.example` 文件并文档化默认值。

## 测试

目前没有统一的测试运行器。验证方式：
1. Docker 冒烟测试：`docker compose up`
2. 手动验证受影响的 UI 路由 / API 端点

## 提交和 PR 指南

提交信息遵循 `<type>: <summary>` 格式（常见类型：`feat:`、`fix:`；`!` 表示破坏性变更）。

PR 应包含：
- **改动说明** — 做了什么、为什么做
- **验证方式** — 具体的验证命令和步骤
- **UI 变更截图** — 如有前端改动，需提供截图
- **环境变量更新** — 如添加新的环境变量，需更新 `*.example` 文件并文档化默认值

## API 文档

后端启动后访问：
- Swagger UI: `http://localhost:8000/api/docs`
- ReDoc: `http://localhost:8000/api/redoc`

## 注意事项

- 前端已内置 `/backend/* -> http://backend:8000/*` 转发
- 生产环境 API 文档会被禁用
- 仅支持 Kiro 服务，不支持其他 AI 服务
