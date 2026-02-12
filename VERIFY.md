# MVC 阶段验证指南

Docker 已启动后，按下面步骤验证前后端与 API 是否正常。

## 1. 确认容器在跑

```bash
docker-compose ps
```

应看到 `stormgate-backend` 和 `stormgate-frontend` 均为 `Up` 且健康。

---

## 2. 验证后端 API

### 2.1 健康检查（必过）

```bash
curl -s http://localhost:8000/api/v1/health | python3 -m json.tool
```

期望：`"status": "healthy"`，且 `database`、`blueprints` 正常。

### 2.2 根路径

```bash
curl -s http://localhost:8000/
```

期望：`{"message":"Stormgate Blueprint Assistant API","version":"1.0.0"}`

### 2.3 API 文档（Swagger）

浏览器打开：**http://localhost:8000/docs**

应能打开交互式 API 文档并尝试接口。

### 2.4 历史记录接口

```bash
curl -s "http://localhost:8000/api/v1/history?limit=5" | python3 -m json.tool
```

期望：返回 `total`、`records` 等字段（可能 `records` 为空）。

---

## 3. 验证前端

浏览器打开：**http://localhost**

应看到「风暴之城新手蓝图助手」页面，可上传截图、调整识别框、查看历史。

---

## 4. 一键脚本验证（可选）

在项目根目录执行：

```bash
./scripts/verify_docker.sh
```

或手动执行脚本内的各条 `curl` 命令。

---

## 5. 用后端自带的 API 测试脚本（需 requests）

```bash
cd backend
pip install requests   # 若未装
python test_api.py
```

会依次请求：健康检查 → 分析（上传假图）→ 历史记录。

---

## 6. 跑后端单元测试（可选）

```bash
cd backend
pip install -r requirements.txt
pytest
```

---

## 常见问题

| 现象 | 处理 |
|------|------|
| `Connection refused` | 确认 `docker-compose up -d` 已执行且 `docker-compose ps` 两服务都在运行 |
| 前端打不开 | 默认端口 80，检查是否被占用；可改 `.env` 里 `FRONTEND_PORT` |
| 后端 500 | 看日志：`docker-compose logs backend` |
| 健康检查 degraded | 看返回里 `services.database` / `services.blueprints` 具体报错 |
