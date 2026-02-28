# 基石图标收集指南

## 当前状态

- **已有数据**: 123个基石的文本数据（名称、效果、稀有度）
- **缺少**: 123个基石的图标图片
- **蓝图/物种**: 已完整（从Wiki抓取）

## 为什么基石没有图标？

之前抓取时，基石页面在Wiki上的图标不完整，且服务器现在被Cloudflare保护屏蔽。

## 解决方案

### 方案1: 本地抓取（推荐）

在你的本地电脑运行抓取脚本：

```bash
# 1. 复制脚本到本地
# 文件: scripts/download_cornerstones_local.py

# 2. 安装依赖
pip install requests beautifulsoup4

# 3. 运行抓取
python download_cornerstones_local.py

# 4. 将下载的图标复制到项目
mv cornerstones/*.png backend/app/data/templates/cornerstones/
```

### 方案2: 游戏内提取

如果你有游戏本体，可以从游戏文件中提取：

**Windows:**
```
Steam安装目录/steamapps/common/Against the Storm/Against the Storm_Data/StreamingAssets/
```

搜索包含 "Cornerstone" 的文件夹，图标通常在 `Sprites` 或 `Icons` 子文件夹。

### 方案3: 游戏截图提取

每次遇到基石选择界面时：

1. 截图（显示基石选择界面）
2. 运行提取工具:
   ```bash
   python scripts/extract_all_from_screenshot.py screenshot.png
   ```
3. 按提示输入基石名称

## 基石选择界面示例

基石通常在以下情况出现：
- **每年 Drizzle 季节开始时**（第1年中期，之后每年开始）
- **Citadel 等级提升时**
- **商人处购买时**

界面与蓝图选择类似：显示3个基石卡片供选择。

## 预期收集进度

| 方式 | 每局获取 | 需要局数 |
|------|----------|----------|
| 正常游戏 | 5-10个 | 15-20局 |
| 使用解锁Mod | 全部 | 1局 |

## 临时替代方案

在图标收集完成前，可以先使用：

1. **文本识别**: 通过OCR识别基石名称
2. **手动选择**: 前端界面提供下拉菜单手动选择

## 需要帮助？

如果你有游戏截图显示基石选择界面，我可以帮你提取图标。只需上传截图并告诉我图中显示的是哪些基石。
