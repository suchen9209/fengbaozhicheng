# 风暴之城新手蓝图助手

AI驱动的决策支持工具，帮助《风暴之城》(Stormgate)游戏玩家通过分析游戏截图来做出最优的蓝图选择。

## 功能特性

- 📸 **截图上传与智能识别** - 支持拖拽上传，自动识别游戏元素（蓝图、资源、种族）
- 🎯 **可调节识别框** - 交互式Canvas识别框，支持拖动和调整大小
- 🤖 **AI驱动的蓝图推荐** - 基于多维度评分算法提供最优推荐
- 📊 **详细的评分分析** - 展示基础价值、种族协同、资源充足度等评分细节
- 📜 **历史记录管理** - 保存和查看过往分析记录，支持分页
- 🎨 **直观的用户界面** - 使用Element Plus构建的现代化UI
- 📱 **响应式设计** - 完美支持桌面和移动设备
- 🔄 **实时错误处理** - 友好的错误提示和加载状态
- 🖼️ **图像处理** - 集成OpenCV模板匹配和Tesseract OCR

## 快速开始

### 使用 Docker Compose（推荐）

1. 克隆仓库
```bash
git clone <repository-url>
cd stormgate-blueprint-assistant
```

2. 配置环境变量（可选）
```bash
cp .env.example .env
# 编辑 .env 文件以自定义配置
```

3. 启动服务
```bash
docker-compose up -d
```

4. 查看日志
```bash
docker-compose logs -f
```

5. 访问应用
- 前端: http://localhost
- 后端API: http://localhost:8000
- API文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/api/v1/health

6. 停止服务
```bash
docker-compose down
```

### 本地开发

#### 后端

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 启动服务
uvicorn app.main:app --reload
```

后端将在 http://localhost:8000 启动

#### 前端

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端将在 http://localhost:5173 启动

## 项目结构

```
stormgate-blueprint-assistant/
├── backend/                 # Python后端
│   ├── app/
│   │   ├── main.py         # FastAPI应用入口
│   │   ├── models.py       # 数据模型
│   │   ├── database.py     # 数据库管理
│   │   ├── api/            # API路由
│   │   │   ├── analyze.py  # 分析端点
│   │   │   └── history.py  # 历史记录端点
│   │   ├── services/       # 业务逻辑服务
│   │   │   ├── recommendation_engine.py
│   │   │   └── history_service.py
│   │   └── data/
│   │       └── blueprints_data.json  # 蓝图数据
│   ├── tests/              # 测试文件
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/               # Vue.js前端
│   ├── src/
│   │   ├── components/     # Vue组件
│   │   ├── views/          # 页面视图
│   │   ├── router/         # 路由配置
│   │   └── services/       # API服务
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml      # Docker编排配置
└── README.md
```

## 技术栈

### 后端
- Python 3.10+
- FastAPI (Web框架)
- SQLAlchemy (ORM)
- SQLite (数据库)
- OpenCV (图像处理，待实现)
- Tesseract (OCR，待实现)

### 前端
- Vue.js 3 (Composition API)
- TypeScript
- Vite (构建工具)
- Element Plus (UI组件库)
- Axios (HTTP客户端)

### 部署
- Docker + Docker Compose
- Nginx (反向代理)

## API文档

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
    "resources": {"木材": 25, "石料": 15},
    "species": "人类",
    "confidence": {"blueprints": 0.85}
  },
  "recommendations": [
    {
      "blueprint_name": "农场",
      "score": 71.0,
      "rank": 1,
      "reasoning": "基础价值分: 68分...",
      "details": {...}
    }
  ],
  "record_id": "..."
}
```

### GET /api/v1/history
获取历史分析记录

**参数**:
- `limit`: 返回记录数 (1-100, 默认20)
- `offset`: 跳过记录数 (默认0)
- `session_id`: 按会话ID过滤
- `user_id`: 按用户ID过滤

### GET /api/v1/health
健康检查端点

## 推荐算法

系统使用多维度评分算法计算蓝图推荐：

1. **基础价值分** = food×10 + fuel×8 + resolve×12
2. **种族协同分** = 匹配种族偏好 +5分
3. **资源充足分** = 每个充足资源(≥10) +3分
4. **复杂度惩罚** = complexity×4

**总分** = 基础价值分 + 种族协同分 + 资源充足分 - 复杂度惩罚

## 开发指南

### 运行测试

```bash
# 后端测试
cd backend
pytest

# 查看覆盖率
pytest --cov=app --cov-report=html

# 前端测试
cd frontend
npm run test:unit
```

### 代码检查

```bash
# Python
cd backend
flake8 app/
mypy app/
black app/

# TypeScript
cd frontend
npm run lint
```

### 添加新蓝图

编辑 `backend/app/data/blueprints_data.json`：

```json
{
  "name": "新蓝图",
  "name_en": "New Blueprint",
  "type": "生产建筑",
  "dlc": "基础版",
  "inputs": {"木材": 5},
  "outputs": {"食物": 10},
  "values": {"food": 4, "fuel": 2, "resolve": 1},
  "complexity": 2,
  "synergy": {
    "species_preferences": ["人类"],
    "biome_bonuses": {}
  },
  "description": "描述文本"
}
```

## 当前状态

✅ **已完成**:
- 项目基础设施和Docker配置
- 数据模型和SQLite数据库
- 推荐引擎（多维度评分算法）
- 历史记录管理（分页、过滤）
- 完整的后端API（分析、历史、健康检查）
- 图像处理服务（OpenCV模板匹配 + Tesseract OCR）
- 前端UI组件（上传、识别框、结果展示、历史记录）
- 识别框调整组件（拖动、缩放、触摸支持）
- 响应式设计（桌面和移动端）
- 错误处理和加载状态
- 24个蓝图数据

🚧 **待完善**:
- 模板图像库（需要收集游戏图标）
- 测试截图样本
- 属性测试（可选）
- CI/CD配置

## 环境变量

创建 `.env` 文件（参考 `.env.example`）：

```bash
# 后端配置
DATABASE_PATH=./data/db/stormgate.db
UPLOAD_DIR=./uploads
LOG_LEVEL=INFO
TEMPLATES_DIR=./data/templates
BLUEPRINTS_DATA_PATH=./data/blueprints_data.json

# Docker端口配置
BACKEND_PORT=8000
FRONTEND_PORT=80

# 前端配置
VITE_API_BASE_URL=http://localhost:8000
```

## 使用指南

### 1. 上传截图
- 点击上传区域或拖拽游戏截图
- 支持PNG、JPG、JPEG格式，最大10MB

### 2. 调整识别框
- 系统会自动显示三个识别框：蓝图区域、资源区域、种族区域
- 拖动识别框移动位置
- 拖动边缘调整大小
- 点击左侧列表选择要调整的识别框

### 3. 开始分析
- 确认识别框位置后，点击"开始分析"
- 系统会识别游戏状态并生成推荐

### 4. 查看结果
- 查看推荐蓝图列表（按评分排序）
- 展开详情查看输入输出、价值评分等信息
- 查看评分理由和建议

### 5. 历史记录
- 所有分析记录自动保存
- 在历史页面查看过往记录
- 点击记录查看详细分析结果

## 贡献指南

欢迎贡献！请遵循以下步骤：

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 故障排除

### Docker相关

**问题**: 容器无法启动
```bash
# 查看日志
docker-compose logs backend
docker-compose logs frontend

# 重新构建
docker-compose build --no-cache
docker-compose up -d
```

**问题**: 端口冲突
```bash
# 修改 .env 文件中的端口
BACKEND_PORT=8001
FRONTEND_PORT=8080
```

### 后端相关

**问题**: 数据库错误
```bash
# 删除数据库文件重新初始化
rm backend/data/db/stormgate.db
docker-compose restart backend
```

**问题**: OCR不可用
- 确保已安装Tesseract OCR
- 检查中文语言包是否安装（tesseract-ocr-chi-sim）

### 前端相关

**问题**: API请求失败
- 检查 `VITE_API_BASE_URL` 环境变量
- 确保后端服务正常运行
- 检查浏览器控制台的网络请求

**问题**: 图片上传失败
- 确保图片格式正确（PNG/JPG/JPEG）
- 确保图片大小不超过10MB
- 检查后端日志查看详细错误

## 许可证

MIT License

## 联系方式

如有问题或建议，请提交 Issue。

## 致谢

- 游戏《风暴之城》(Stormgate)
- Element Plus UI组件库
- FastAPI框架
