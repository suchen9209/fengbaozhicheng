#!/bin/bash
# 从 Against the Storm 游戏文件中提取图标
#
# 用法:
#   ./extract_icons_from_game.sh [游戏数据路径]
#
# 示例:
#   ./extract_icons_from_game.sh "/Users/username/Library/Application Support/Steam/steamapps/common/Against the Storm/Against the Storm_Data"

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
GAME_PATH="${1:-}"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_green() { echo -e "${GREEN}$1${NC}"; }
print_red() { echo -e "${RED}$1${NC}"; }
print_yellow() { echo -e "${YELLOW}$1${NC}"; }

# 如果没有提供路径，尝试自动查找
if [ -z "$GAME_PATH" ]; then
    print_yellow "未提供游戏路径，尝试自动查找..."
    
    # macOS Steam 路径
    if [ -d "$HOME/Library/Application Support/Steam/steamapps/common/Against the Storm" ]; then
        GAME_PATH="$HOME/Library/Application Support/Steam/steamapps/common/Against the Storm/Against the Storm_Data"
    # Linux Steam 路径
    elif [ -d "$HOME/.local/share/Steam/steamapps/common/Against the Storm" ]; then
        GAME_PATH="$HOME/.local/share/Steam/steamapps/common/Against the Storm/Against the Storm_Data"
    # Windows Wine/CrossOver 路径
    elif [ -d "$HOME/.wine/drive_c/Program Files (x86)/Steam/steamapps/common/Against the Storm" ]; then
        GAME_PATH="$HOME/.wine/drive_c/Program Files (x86)/Steam/steamapps/common/Against the Storm/Against the Storm_Data"
    fi
    
    if [ -z "$GAME_PATH" ]; then
        print_red "错误: 无法找到游戏路径"
        echo "请手动指定游戏数据路径:"
        echo "  $0 \"/path/to/Against the Storm/Against the Storm_Data\""
        exit 1
    fi
    
    print_green "找到游戏路径: $GAME_PATH"
fi

# 验证路径
if [ ! -d "$GAME_PATH" ]; then
    print_red "错误: 路径不存在: $GAME_PATH"
    exit 1
fi

# 检查是否有 .assets 文件
ASSETS_COUNT=$(find "$GAME_PATH" -name "*.assets" 2>/dev/null | wc -l)
if [ "$ASSETS_COUNT" -eq 0 ]; then
    print_red "错误: 在路径中未找到 .assets 文件"
    echo "请确保指向的是 Against the Storm_Data 目录"
    exit 1
fi

print_green "找到 $ASSETS_COUNT 个 .assets 文件"

# 检查 Python 和依赖
if ! command -v python3 &> /dev/null; then
    print_red "错误: 需要安装 Python 3"
    exit 1
fi

# 安装 UnityPy（如果需要）
if ! python3 -c "import UnityPy" 2>/dev/null; then
    print_yellow "安装 UnityPy..."
    pip3 install UnityPy -q
fi

# 创建输出目录
OUTPUT_DIR="$PROJECT_DIR/backend/app/data/templates"
mkdir -p "$OUTPUT_DIR/blueprints"
mkdir -p "$OUTPUT_DIR/species"
mkdir -p "$OUTPUT_DIR/cornerstones"
mkdir -p "$OUTPUT_DIR/resources"

print_green "输出目录: $OUTPUT_DIR"

# 运行 Python 提取脚本
print_yellow "开始提取图标..."
python3 "$SCRIPT_DIR/extract_from_game_files.py" "$GAME_PATH" "$OUTPUT_DIR"

echo ""
print_green "=== 提取完成 ==="
echo ""
echo "图标已保存到:"
echo "  - 蓝图: $OUTPUT_DIR/blueprints/"
echo "  - 物种: $OUTPUT_DIR/species/"
echo "  - 基石: $OUTPUT_DIR/cornerstones/"
echo "  - 资源: $OUTPUT_DIR/resources/"
echo ""
echo "统计:"
find "$OUTPUT_DIR" -name "*.png" -exec basename {} \; | wc -l | xargs echo "  总图标数:"
