#!/bin/bash
set -e

echo "========================================="
echo "  KiroHub - 部署脚本"
echo "========================================="

if ! command -v docker &> /dev/null; then
    echo "错误: 未找到 docker，请先安装 Docker。"
    exit 1
fi

if [ ! -f .env ]; then
    echo "正在生成 .env 配置文件..."
    JWT_SECRET=$(openssl rand -base64 32)
    ENCRYPTION_KEY=$(openssl rand -base64 32)
    cat > .env << ENVEOF
JWT_SECRET_KEY=${JWT_SECRET}
PLUGIN_API_ENCRYPTION_KEY=${ENCRYPTION_KEY}
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123456
KIRO_PROXY_URL=
COOKIE_HTTP=HTTPS
ENVEOF
    echo ".env 文件已创建。请根据需要修改配置。"
fi

echo ""
echo "选择操作:"
echo "1) 启动所有服务"
echo "2) 停止所有服务"
echo "3) 重新构建并重启"
echo "4) 查看日志"
echo "5) 生成加密密钥"
read -p "选择 [1-5]: " choice

case $choice in
    1)
        docker compose up -d
        echo "服务已启动。"
        echo "前端: http://localhost:3000"
        echo "后端: http://localhost:8000"
        ;;
    2)
        docker compose down
        echo "服务已停止。"
        ;;
    3)
        docker compose down
        docker compose pull
        docker compose up -d --build
        echo "服务已重新构建并启动。"
        ;;
    4)
        docker compose logs -f
        ;;
    5)
        echo "生成新的加密密钥..."
        docker compose run --rm backend python generate_encryption_key.py
        ;;
    *)
        echo "无效选择。"
        ;;
esac
