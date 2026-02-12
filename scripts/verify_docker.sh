#!/usr/bin/env bash
# 在 Docker 已启动时验证 MVC 阶段：后端 API + 前端可访问
set -e

BASE="http://localhost:8000"
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

ok() { echo -e "${GREEN}[OK]${NC} $1"; }
fail() { echo -e "${RED}[FAIL]${NC} $1"; exit 1; }

echo "=== 1. 容器状态 ==="
docker-compose ps || fail "docker-compose 未运行或未在项目目录"

echo ""
echo "=== 2. 后端健康检查 ==="
code=$(curl -s -o /dev/null -w "%{http_code}" "$BASE/api/v1/health")
if [ "$code" = "200" ]; then
  ok "GET $BASE/api/v1/health -> $code"
  curl -s "$BASE/api/v1/health" | python3 -m json.tool 2>/dev/null || curl -s "$BASE/api/v1/health"
else
  fail "GET $BASE/api/v1/health -> $code"
fi

echo ""
echo "=== 3. 根路径 ==="
code=$(curl -s -o /dev/null -w "%{http_code}" "$BASE/")
[ "$code" = "200" ] && ok "GET $BASE/ -> $code" || fail "GET $BASE/ -> $code"

echo ""
echo "=== 4. 历史接口 ==="
code=$(curl -s -o /dev/null -w "%{http_code}" "$BASE/api/v1/history?limit=5")
[ "$code" = "200" ] && ok "GET $BASE/api/v1/history -> $code" || fail "GET $BASE/api/v1/history -> $code"

echo ""
echo "=== 5. 前端 (localhost:80) ==="
code=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost/" 2>/dev/null || true)
if [ "$code" = "200" ]; then
  ok "GET http://localhost/ -> $code"
else
  echo "  若端口不是 80，请用浏览器访问实际配置的地址（如 http://localhost:8080）"
fi

echo ""
echo "=== 验证完成 ==="
echo "  前端页面: http://localhost"
echo "  API 文档: $BASE/docs"
