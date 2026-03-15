<h1 align="center">KiroHub</h1>

<p align="center">
  基于 Docker 的 Kiro 账号管理系统，支持 AWS-IMA 和企业账户
</p>

## 项目简介

KiroHub 是一个专注于 Kiro 账号管理的系统，提供：
- **Kiro AWS-IMA (Builder ID / AWS IdC)** 账号管理
- **Kiro 企业账户（Enterprise）** 批量导入
- OpenAI 兼容的 API 接口
- Redis 缓存支持
- 使用量统计和监控

## 技术栈

- **前端**: Next.js 16 + React 19 + Tailwind CSS 4
- **后端**: FastAPI + Python 3.10+ + SQLAlchemy 2.0
- **数据库**: PostgreSQL 17
- **缓存**: Redis 7
- **部署**: Docker + Docker Compose

## 快速开始

### 1. 配置环境变量

```bash
cp .env.example .env
```

**必须配置的密钥**：

```bash
# 生成 Fernet 加密密钥（用于加密存储 Kiro 凭证）
docker compose run --rm backend python generate_encryption_key.py

# 生成 JWT 密钥
openssl rand -base64 32
```

更新 `.env` 文件：
- `JWT_SECRET_KEY` - JWT 令牌签名密钥
- `PLUGIN_API_ENCRYPTION_KEY` - Fernet 加密密钥
- `ADMIN_USERNAME` / `ADMIN_PASSWORD` - 管理员账号（密码至少 6 位）

**访问配置**：
- `COOKIE_HTTP`:
  - HTTPS 域名访问：保持 `COOKIE_HTTP=HTTPS`
  - HTTP IP 直连：设置 `COOKIE_HTTP=HTTP`

### 2. 启动服务

```bash
docker compose up -d
```

### 3. 访问系统

- 前端：`http://localhost:3000`
- 后端 API 文档：`http://localhost:8000/api/docs`（开发环境）

## Docker 镜像

```bash
# 拉取镜像
docker pull terrysiu/kirohub-web:latest
docker pull terrysiu/kirohub-backend:latest

# 或使用自定义镜像
export IMAGE_OWNER=your-dockerhub-username
export IMAGE_TAG=v0.0.1
docker compose up -d
```

## 支持的 Kiro 账号类型

1. **AWS-IMA (Builder ID / AWS IdC)**
   - 通过 AWS Identity Center 认证
   - 支持 refresh_token + client_id + client_secret

2. **企业账户（Enterprise）**
   - 批量导入企业账号
   - JSON 格式导入

## API 使用

系统提供 OpenAI 兼容的 API 接口：

```bash
# 获取模型列表
curl http://localhost:8000/v1/models \
  -H "Authorization: Bearer YOUR_API_KEY"

# 聊天补全
curl http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude-opus-4-6",
    "messages": [{"role": "user", "content": "Hello"}],
    "stream": true
  }'

# 查看缓存统计
curl http://localhost:8000/v1/cache/stats \
  -H "Authorization: Bearer YOUR_API_KEY"
```

## 开发

### 后端开发

```bash
cd KiroHub-Backend
uv sync
uv run uvicorn app.main:app --reload --port 8000

# 数据库迁移
uv run alembic upgrade head
uv run alembic revision --autogenerate -m "描述"
```

### 前端开发

```bash
cd KiroHub
pnpm install
pnpm dev
```

## 鸣谢

本项目基于以下开源项目：
- [AntiHub-ALL](https://github.com/zhongruan0522/AntiHub-ALL)
- [Kiro.rs](https://github.com/hank9999/kiro.rs)
- [KiroGate](https://github.com/aliom-v/KiroGate)

## 许可证

MIT License
