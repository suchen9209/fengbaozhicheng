# 风暴之城蓝图助手 - 后端

Python FastAPI后端服务，提供蓝图推荐和历史记录管理功能。

## 快速开始

### 1. 安装依赖

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Linux/Mac:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 启动服务

```bash
# 使用启动脚本
chmod +x run.sh
./run.sh

# 或直接使用uvicorn
uvicorn app.main:app --reload
```

服务将在 http://localhost:8000 启动

### 3. 测试API

```bash
# 查看API文档
open http://localhost:8000/docs

# 运行测试脚本
python test_api.py

# 运行单元测试
pytest
```

## API端点

### GET /api/v1/health
健康检查端点

### POST /api/v1/analyze
上传截图并获取蓝图推荐

**请求**:
- `image`: 图片文件 (PNG/JPG/JPEG, max 10MB)
- `boxes`: JSON字符串，包含3个识别框坐标
- `session_id`: 可选的会话ID

**响应**:
```json
{
  "request_id": "...",
  "game_state": {
    "available_blueprints": ["农场", "矿场"],
    "resources": {"木材": 25},
    "species": "人类"
  },
  "recommendations": [...]
}
```

### GET /api/v1/history
获取历史分析记录

**参数**:
- `limit`: 返回记录数 (1-100, 默认20)
- `offset`: 跳过记录数 (默认0)
- `session_id`: 按会话ID过滤
- `user_id`: 按用户ID过滤

## 项目结构

```
backend/
├── app/
│   ├── main.py              # FastAPI应用入口
│   ├── models.py            # 数据模型
│   ├── database.py          # 数据库管理
│   ├── api/                 # API路由
│   │   ├── analyze.py       # 分析端点
│   │   └── history.py       # 历史记录端点
│   ├── services/            # 业务逻辑
│   │   ├── recommendation_engine.py
│   │   └── history_service.py
│   └── data/
│       └── blueprints_data.json  # 蓝图数据
├── tests/                   # 测试文件
├── requirements.txt         # Python依赖
└── README.md
```

## 开发

### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_models.py

# 查看覆盖率
pytest --cov=app --cov-report=html
```

### 代码检查

```bash
# Linting
flake8 app/

# Type checking
mypy app/

# Formatting
black app/
```

## 环境变量

在 `.env` 文件中配置：

```
DATABASE_PATH=./data/stormgate.db
UPLOAD_DIR=./uploads
LOG_LEVEL=INFO
BLUEPRINTS_DATA_PATH=app/data/blueprints_data.json
```

## 注意事项

- 图像识别功能尚未实现，当前返回模拟数据
- 生产环境需要配置CORS白名单
- 建议使用Nginx作为反向代理
