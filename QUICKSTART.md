# 快速开始指南

本指南将帮助您在5分钟内启动风暴之城蓝图助手。

## 前置要求

- Docker 和 Docker Compose
- 或者：Node.js 20+ 和 Python 3.10+

## 方式一：使用 Docker（推荐）

### 1. 克隆项目

```bash
git clone <repository-url>
cd stormgate-blueprint-assistant
```

### 2. 启动服务

```bash
docker-compose up -d
```

等待几分钟让容器构建和启动。

### 3. 访问应用

打开浏览器访问：http://localhost

就这么简单！🎉

### 4. 停止服务

```bash
docker-compose down
```

## 方式二：本地开发

### 1. 启动后端

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

后端运行在：http://localhost:8000

### 2. 启动前端（新终端）

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端运行在：http://localhost:5173

## 使用流程

1. **上传截图** - 拖拽或点击上传游戏截图
2. **调整识别框** - 确保识别框覆盖正确的游戏区域
3. **开始分析** - 点击按钮获取推荐
4. **查看结果** - 查看推荐蓝图和详细评分

## 下一步

- 查看 [README.md](README.md) 了解完整文档
- 查看 [API文档](http://localhost:8000/docs) 了解API详情
- 添加更多蓝图数据到 `backend/app/data/blueprints_data.json`

## 需要帮助？

- 查看 README.md 中的故障排除部分
- 提交 Issue 报告问题
- 查看日志：`docker-compose logs -f`

## 模板图与识别精度

蓝图/种族识别依赖 `backend/app/data/templates/` 下的模板图。**若希望和官方一致、截图时更好处理**，优先用以下图源（详见 [docs/TEMPLATE_SOURCES.md](docs/TEMPLATE_SOURCES.md)）：

- **官方渠道**：运行 `python scripts/download_official_wiki_images.py` 从 [Hooded Horse 官方 Wiki](https://wiki.hoodedhorse.com/wiki/Against_the_Storm/) 抓取建筑/种族图标到 `templates/`（与游戏同源）；若 403 则在本地网络重试或浏览器手动另存。
- **最推荐**：**游戏内截图裁剪**——在蓝图/种族选择界面截图，按图标格子裁剪成单张图并按要求命名，替换进 `templates/blueprints/` 与 `templates/species/`，与截图时的 UI 完全一致，识别最准。
- **当前默认**：使用 [Fandom Wiki](https://against-the-storm.fandom.com/wiki/) 抓取时，各页图标尺寸/格式不统一，下载后**必须**做一次归一化。

归一化（任选图源后都建议执行一次）：

```bash
pip install -r scripts/requirements-scraper.txt
python scripts/download_ats_wiki_images.py    # 仅当用 Fandom 且尚未下载时
python scripts/normalize_template_images.py   # 统一为 128×128 真 PNG（可选 --backup）
```

## 注意事项

- 首次启动可能需要几分钟构建Docker镜像
- 确保端口80和8000未被占用
- 图像识别依赖模板图（见上「模板图与识别精度」）

祝您使用愉快！🚀
