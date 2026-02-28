#!/usr/bin/env python3
"""
从 Against the Storm 游戏文件中提取图标

需要安装: 
  pip install UnityPy

用法:
  python extract_from_game_files.py <game_data_path>

示例:
  python extract_from_game_files.py "/Users/username/Library/Application Support/Steam/steamapps/common/Against the Storm/Against the Storm_Data"
"""

import sys
import os
from pathlib import Path

try:
    import UnityPy
except ImportError:
    print("错误: 需要安装 UnityPy")
    print("运行: pip install UnityPy")
    sys.exit(1)


def extract_icons(game_data_path: str, output_dir: str = "backend/app/data/templates"):
    """
    从游戏资源文件中提取图标
    
    Args:
        game_data_path: 游戏数据目录路径 (包含 *.assets 文件)
        output_dir: 输出目录
    """
    game_data = Path(game_data_path)
    if not game_data.exists():
        print(f"错误: 路径不存在: {game_data}")
        return
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    blueprints_dir = output_path / "blueprints"
    cornerstones_dir = output_path / "cornerstones"
    blueprints_dir.mkdir(exist_ok=True)
    cornerstones_dir.mkdir(exist_ok=True)
    
    # 查找所有 .assets 文件
    assets_files = list(game_data.glob("**/*.assets"))
    print(f"找到 {len(assets_files)} 个 .assets 文件")
    
    extracted_count = 0
    
    for assets_file in assets_files:
        print(f"\n处理: {assets_file.name}")
        
        try:
            # 加载资源文件
            env = UnityPy.load(str(assets_file))
            
            for obj in env.objects:
                # 只处理 Texture2D 类型的对象
                if obj.type.name == "Texture2D":
                    data = obj.read()
                    name = data.name
                    
                    # 检查是否是图标（根据名称过滤）
                    name_lower = name.lower()
                    
                    # 蓝图图标
                    if any(keyword in name_lower for keyword in [
                        "building", "structure", "blueprint", "camp", "production",
                        "house", "workshop", "farm", "mill", "kitchen", "oven"
                    ]):
                        try:
                            # 获取图像数据
                            image = data.image
                            if image:
                                output_file = blueprints_dir / f"{name_lower.replace(' ', '_')}.png"
                                image.save(output_file)
                                print(f"  ✓ 蓝图: {name}")
                                extracted_count += 1
                        except Exception as e:
                            print(f"  ✗ 蓝图 {name}: {e}")
                    
                    # 基石图标
                    elif any(keyword in name_lower for keyword in [
                        "cornerstone", "perk", "boon", "blessing", "upgrade"
                    ]):
                        try:
                            image = data.image
                            if image:
                                output_file = cornerstones_dir / f"{name_lower.replace(' ', '_')}.png"
                                image.save(output_file)
                                print(f"  ✓ 基石: {name}")
                                extracted_count += 1
                        except Exception as e:
                            print(f"  ✗ 基石 {name}: {e}")
            
        except Exception as e:
            print(f"  无法处理文件: {e}")
    
    print(f"\n=== 提取完成 ===")
    print(f"总共提取: {extracted_count} 个图标")
    print(f"蓝图位置: {blueprints_dir}")
    print(f"基石位置: {cornerstones_dir}")


def find_game_path():
    """尝试自动查找游戏路径"""
    possible_paths = []
    
    # macOS
    home = Path.home()
    possible_paths.extend([
        home / "Library/Application Support/Steam/steamapps/common/Against the Storm/Against the Storm_Data",
        home / "Library/Application Support/Steam/steamapps/common/Against the Storm/Against the Storm.app/Contents/Data",
    ])
    
    # Windows (通过Wine/CrossOver)
    possible_paths.extend([
        home / ".wine/drive_c/Program Files (x86)/Steam/steamapps/common/Against the Storm/Against the Storm_Data",
        home / ".local/share/Steam/steamapps/common/Against the Storm/Against the Storm_Data",
    ])
    
    for path in possible_paths:
        if path.exists():
            return str(path)
    
    return None


if __name__ == "__main__":
    if len(sys.argv) > 1:
        game_path = sys.argv[1]
    else:
        print("正在查找游戏路径...")
        game_path = find_game_path()
        if game_path:
            print(f"找到游戏路径: {game_path}")
        else:
            print("未找到游戏路径，请手动指定")
            print(f"用法: {sys.argv[0]} <game_data_path>")
            sys.exit(1)
    
    extract_icons(game_path)
