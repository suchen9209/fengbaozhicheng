#!/usr/bin/env python3
"""
从 Against the Storm Wiki 下载模板图片，供 OpenCV 模板匹配使用：
- 种族图标 -> templates/species/（识别当前种族）
- 建筑图标 -> templates/blueprints/（识别可用蓝图/建筑）

说明：Fandom Wiki 各页表格里的图标尺寸不统一（117/128/256 等），且可能是 WebP 存成 .png。
下载后建议执行归一化，统一尺寸与格式，匹配更稳：
  python scripts/normalize_template_images.py [--templates-dir DIR] [--size 128]

模板目录需与 backend 中 TemplateMatcher 一致：backend/app/data/templates/
文件名：species 用英文小写（human.png, beaver.png）；blueprints 用建筑名 slug（woodcutters_camp.png）。

用法：
  pip install -r scripts/requirements-scraper.txt
  python scripts/download_ats_wiki_images.py [--templates-dir DIR] [--dry-run]
  python scripts/normalize_template_images.py   # 推荐：统一为 128x128 真 PNG
"""
import argparse
import re
import sys
from pathlib import Path
from typing import Optional

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://against-the-storm.fandom.com"
WIKI_IMAGE_BASE = "https://static.wikia.nocookie.net/against-the-storm/images"
USER_AGENT = "ATS-Wiki-Scraper/1.0 (data collection for game assistant)"


def session():
    s = requests.Session()
    s.headers.update({"User-Agent": USER_AGENT})
    return s


def slug(s: str) -> str:
    """建筑名转文件名：Woodcutters' Camp -> woodcutters_camp"""
    s = re.sub(r"[\s']+", "_", s)
    s = re.sub(r"[^a-zA-Z0-9_]", "", s)
    return s.lower() or "unknown"


def to_full_image_url(thumb_url: str) -> str:
    """缩略图 URL 转成全图 URL（去掉 scale-to-width-down）"""
    if not thumb_url or "static.wikia.nocookie.net" not in thumb_url:
        return thumb_url
    return re.sub(r"/scale-to-width-down/\d+\?", "?", thumb_url)


def to_fixed_width_url(thumb_url: str, width: int) -> str:
    """将图片 URL 改为指定宽度（Fandom 支持 scale-to-width-down/N），便于下载后尺寸一致"""
    if not thumb_url or "static.wikia.nocookie.net" not in thumb_url:
        return thumb_url
    # 若已有 scale-to-width-down，替换为 width；否则在 revision/latest 后加
    if "/scale-to-width-down/" in thumb_url:
        return re.sub(r"/scale-to-width-down/\d+", f"/scale-to-width-down/{width}", thumb_url)
    return re.sub(r"(/revision/latest)(\?)", rf"\1/scale-to-width-down/{width}\2", thumb_url)


def fetch_html(sess: requests.Session, path: str) -> str:
    r = sess.get(BASE_URL + path, timeout=30)
    r.raise_for_status()
    return r.text


def download_images(
    sess: requests.Session,
    templates_dir: Path,
    dry_run: bool,
    fixed_width: Optional[int] = None,
) -> None:
    # ---------- 1. 种族图标（Species 页表格第一列）----------
    species_dir = templates_dir / "species"
    if not dry_run:
        species_dir.mkdir(parents=True, exist_ok=True)

    html = fetch_html(sess, "/wiki/Species")
    soup = BeautifulSoup(html, "html.parser")
    species_done = set()
    for table in soup.find_all("table"):
        for tr in table.find_all("tr")[1:]:
            cells = tr.find_all(["td", "th"])
            if not cells:
                continue
            first = cells[0]
            url = None
            # 种族名：本行内找指向 /wiki/Beaver 等链接的文本
            a_wiki = tr.find("a", href=re.compile(r"wiki/(Beaver|Harpy|Human|Lizard|Fox)$"))
            name = (a_wiki.get_text(strip=True) if a_wiki else None) or ""
            if not name or name in species_done:
                continue
            # 图片 URL：优先 data-src（懒加载时真实图），否则 src；或 <a href="...*.png">
            img = first.find("img")
            if img:
                url = img.get("data-src") or img.get("src") or ""
                if url and (url.startswith("data:") or "gif" in url.lower()):
                    url = img.get("data-src") or ""
            if not url:
                a_img = first.find("a", href=re.compile(r"\.(png|jpg|jpeg)(\?|$)", re.I))
                if a_img:
                    url = (a_img.get("href") or "").strip()
            if not url:
                continue
            if not url.startswith("http"):
                url = "https:" + url
            url = to_fixed_width_url(url, fixed_width) if fixed_width else to_full_image_url(url)
            species_done.add(name)
            fname = f"{name.lower()}.png"
            out = species_dir / fname
            print(f"  [species] {name} -> {out.name}")
            if not dry_run and url:
                try:
                    r = sess.get(url, timeout=15)
                    r.raise_for_status()
                    out.write_bytes(r.content)
                except Exception as e:
                    print(f"    FAIL: {e}", file=sys.stderr)

    # ---------- 2. 建筑图标（各分类页表格 Icon 列）----------
    blueprints_dir = templates_dir / "blueprints"
    if not dry_run:
        blueprints_dir.mkdir(parents=True, exist_ok=True)

    building_pages = [
        "/wiki/Camps",
        "/wiki/Food_Production",
        "/wiki/Housing",
        "/wiki/Industry",
        "/wiki/City_Buildings",
    ]
    seen_slugs = set()
    for path in building_pages:
        try:
            html = fetch_html(sess, path)
        except Exception as e:
            print(f"  [buildings] skip {path}: {e}", file=sys.stderr)
            continue
        soup = BeautifulSoup(html, "html.parser")
        for table in soup.find_all("table", class_=re.compile("fandom-table|sortable|wikitable")):
            rows = table.find_all("tr")
            if not rows:
                continue
            headers = [th.get_text(strip=True) for th in rows[0].find_all(["th", "td"])]
            name_idx = next((i for i, h in enumerate(headers) if "name" in h.lower()), 1)
            for tr in rows[1:]:
                cells = tr.find_all(["td", "th"])
                if len(cells) <= name_idx:
                    continue
                name_cell = cells[name_idx]
                a = name_cell.find("a", href=re.compile(r"^/wiki/"))
                if not a:
                    continue
                building_name = a.get_text(strip=True)
                if not building_name:
                    continue
                s = slug(building_name)
                if s in seen_slugs:
                    continue
                seen_slugs.add(s)
                # Icon 通常在第一列；支持懒加载 data-src
                icon_cell = cells[0] if len(cells) > 0 else None
                if not icon_cell:
                    continue
                img = icon_cell.find("img")
                if img:
                    url = img.get("data-src") or img.get("src") or ""
                    if url and (url.startswith("data:") or "gif" in url.lower()):
                        url = img.get("data-src") or ""
                else:
                    a_img = icon_cell.find("a", href=re.compile(r"\.(png|jpg|jpeg)(\?|$)", re.I))
                    url = (a_img.get("href") or "") if a_img else ""
                if not url:
                    continue
                if not url.startswith("http"):
                    url = "https:" + url
                url = to_fixed_width_url(url, fixed_width) if fixed_width else to_full_image_url(url)
                out = blueprints_dir / f"{s}.png"
                print(f"  [blueprints] {building_name} -> {out.name}")
                if not dry_run and url:
                    try:
                        r = sess.get(url, timeout=15)
                        r.raise_for_status()
                        out.write_bytes(r.content)
                    except Exception as e:
                        print(f"    FAIL: {e}", file=sys.stderr)

    print(f"\nSpecies: {species_dir} ({len(list(species_dir.glob('*.png'))) if species_dir.exists() else 0} files)")
    print(f"Blueprints: {blueprints_dir} ({len(list(blueprints_dir.glob('*.png'))) if blueprints_dir.exists() else 0} files)")


def main():
    parser = argparse.ArgumentParser(description="Download ATS wiki template images for matching")
    parser.add_argument(
        "--templates-dir",
        type=str,
        default="backend/app/data/templates",
        help="Templates directory (default: backend/app/data/templates)",
    )
    parser.add_argument("--dry-run", action="store_true", help="Only print what would be downloaded")
    parser.add_argument(
        "--fixed-width",
        type=int,
        default=None,
        metavar="N",
        help="Request images at fixed width N (e.g. 128) for more consistent size; still recommend normalize_template_images.py after",
    )
    args = parser.parse_args()

    root = Path(__file__).resolve().parent.parent
    templates_dir = root / args.templates_dir
    print(f"Templates dir: {templates_dir}")

    sess = session()
    download_images(sess, templates_dir, args.dry_run, args.fixed_width)
    return 0


if __name__ == "__main__":
    sys.exit(main())
