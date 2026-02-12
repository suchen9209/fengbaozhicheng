#!/usr/bin/env python3
"""
将模板图归一化：统一尺寸、统一为真 PNG，便于 OpenCV 模板匹配稳定。

Wiki 抓下来的图问题：
- 尺寸不一：117x117、128x128、256x256、68x69 等
- 部分为 WebP 却存成 .png 扩展名
- 直接用于 matchTemplate 时，不同基准尺寸会导致置信度不可比、匹配不稳

做法：
- 用 Pillow 读取（支持 WebP/PNG/JPG）
- 转为灰度后，等比缩放到目标尺寸内并居中 padding，或直接 resize 到目标尺寸（默认 128x128）
- 保存为真 PNG，覆盖原文件（可选 --backup 先备份）

用法：
  pip install Pillow
  python scripts/normalize_template_images.py [--templates-dir DIR] [--size 128] [--backup]
"""
import argparse
import shutil
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("请先安装 Pillow: pip install Pillow", file=sys.stderr)
    sys.exit(1)

DEFAULT_SIZE = 128


def normalize_image(path: Path, target_size: int, backup: bool) -> None:
    """将单张图归一化为 target_size x target_size 灰度 PNG。"""
    try:
        im = Image.open(path)
    except Exception as e:
        print(f"  跳过（无法打开）: {path.name} - {e}", file=sys.stderr)
        return
    if backup:
        backup_path = path.with_suffix(path.suffix + ".bak")
        shutil.copy2(path, backup_path)
    # 转灰度（若为 RGBA 先白底合成）
    if im.mode == "L":
        pass
    elif im.mode in ("RGBA", "LA", "P"):
        background = Image.new("RGB", im.size, (255, 255, 255))
        if im.mode == "P":
            im = im.convert("RGBA")
        if im.mode in ("RGBA", "LA"):
            background.paste(im, mask=im.split()[-1])
        else:
            background.paste(im)
        im = background.convert("L")
    else:
        im = im.convert("L")
    # 等比缩放并放入 target_size x target_size 画布（居中）
    w, h = im.size
    scale = min(target_size / w, target_size / h)
    nw, nh = max(1, int(w * scale)), max(1, int(h * scale))
    im = im.resize((nw, nh), Image.Resampling.LANCZOS)
    canvas = Image.new("L", (target_size, target_size), 255)
    x = (target_size - nw) // 2
    y = (target_size - nh) // 2
    canvas.paste(im, (x, y))
    canvas.save(path, "PNG")
    print(f"  {path.name} -> {target_size}x{target_size} PNG")


def main():
    parser = argparse.ArgumentParser(description="Normalize template images to fixed size PNG")
    parser.add_argument(
        "--templates-dir",
        type=str,
        default="backend/app/data/templates",
        help="Templates root (default: backend/app/data/templates)",
    )
    parser.add_argument(
        "--size",
        type=int,
        default=DEFAULT_SIZE,
        help=f"Target side length (default: {DEFAULT_SIZE})",
    )
    parser.add_argument("--backup", action="store_true", help="Backup originals as .png.bak")
    parser.add_argument("--dry-run", action="store_true", help="Only list files, do not modify")
    args = parser.parse_args()

    root = Path(__file__).resolve().parent.parent
    templates_dir = root / args.templates_dir
    if not templates_dir.exists():
        print(f"目录不存在: {templates_dir}", file=sys.stderr)
        sys.exit(1)

    count = 0
    for sub in ("species", "blueprints"):
        subdir = templates_dir / sub
        if not subdir.exists():
            continue
        for path in sorted(subdir.glob("*.png")):
            if path.suffix.lower() == ".bak":
                continue
            count += 1
            if args.dry_run:
                print(f"  [would normalize] {sub}/{path.name}")
                continue
            normalize_image(path, args.size, args.backup)
    if args.dry_run:
        print(f"\n共 {count} 个文件将被归一化")
    else:
        print(f"\n已归一化 {count} 个模板为 {args.size}x{args.size} PNG")
    return 0


if __name__ == "__main__":
    sys.exit(main())
