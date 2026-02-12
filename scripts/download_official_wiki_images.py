#!/usr/bin/env python3
"""
从 Hooded Horse 官方 Wiki 抓取建筑/种族图标，与游戏同源，截图识别更准。

页面：
- 建筑: https://wiki.hoodedhorse.com/wiki/Against_the_Storm/List_of_Buildings
- 种族: https://wiki.hoodedhorse.com/wiki/Against_the_Storm/Species

保存到 backend/app/data/templates/blueprints/ 与 species/，文件名与现有一致（建筑用 slug，
种族用小写英文）。下载后建议执行一次归一化：
  python scripts/normalize_template_images.py

若出现 403 Forbidden：多为站点对部分 IP/机房限流，请在本地网络执行本脚本，或浏览器打开
上述页面手动另存图标到 templates 对应目录。

用法：
  pip install -r scripts/requirements-scraper.txt
  python scripts/download_official_wiki_images.py [--templates-dir DIR] [--dry-run] [--timeout 25]
"""
import argparse
import re
import sys
import time
from pathlib import Path
from typing import Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://wiki.hoodedhorse.com"
# 官方 Wiki 页面路径（MediaWiki 用下划线）
LIST_OF_BUILDINGS = "/wiki/Against_the_Storm/List_of_Buildings"
SPECIES_PAGE = "/wiki/Against_the_Storm/Species"
# 使用浏览器风格 UA 和 Accept，避免官方 Wiki 返回 403
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)
WIKI_ACCEPT = "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
# 请求图片时可选统一宽度（部分 MediaWiki 支持 ?width=）
IMAGE_WIDTH = 128


def slug(s: str) -> str:
    """建筑名转文件名：Woodcutters' Camp -> woodcutters_camp"""
    s = re.sub(r"[\s']+", "_", s)
    s = re.sub(r"[^a-zA-Z0-9_]", "", s)
    return s.lower() or "unknown"


def session():
    s = requests.Session()
    s.headers.update({
        "User-Agent": USER_AGENT,
        "Accept": WIKI_ACCEPT,
        "Accept-Language": "en-US,en;q=0.9",
    })
    return s


def fetch_html(sess: requests.Session, path: str, timeout: int = 25, retries: int = 2) -> str:
    url = urljoin(BASE_URL, path)
    for attempt in range(retries + 1):
        try:
            r = sess.get(url, timeout=timeout, headers={"Accept": WIKI_ACCEPT})
            r.raise_for_status()
            return r.text
        except (requests.RequestException, OSError) as e:
            if attempt < retries:
                time.sleep(2)
                continue
            raise RuntimeError(f"Failed to fetch {url}: {e}") from e


def resolve_image_url(url: str, width: Optional[int] = None) -> str:
    """相对 URL 转绝对；可选加 ?width= 取统一尺寸"""
    if not url or url.startswith("data:"):
        return url
    if not url.startswith("http"):
        url = urljoin(BASE_URL, url)
    if width and "Special:FilePath" in url and "?" not in url:
        url = f"{url}?width={width}"
    return url


def download_file(sess: requests.Session, url: str, out_path: Path, timeout: int = 25) -> bool:
    try:
        r = sess.get(url, timeout=timeout)
        r.raise_for_status()
        out_path.write_bytes(r.content)
        return True
    except Exception as e:
        print(f"    FAIL: {e}", file=sys.stderr)
        return False


def scrape_buildings(sess: requests.Session, templates_dir: Path, dry_run: bool, timeout: int = 25) -> int:
    """从 List of Buildings 页解析表格：每行取「建筑名 + 图标」，按 slug 保存（去重）"""
    html = fetch_html(sess, LIST_OF_BUILDINGS, timeout=timeout)
    soup = BeautifulSoup(html, "html.parser")
    blueprints_dir = templates_dir / "blueprints"
    if not dry_run:
        blueprints_dir.mkdir(parents=True, exist_ok=True)

    seen_slugs = set()
    count = 0
    for table in soup.find_all("table"):
        for tr in table.find_all("tr"):
            cells = tr.find_all(["td", "th"])
            if len(cells) < 2:
                continue
            building_name = None
            for a in tr.find_all("a", href=True):
                href = a.get("href", "")
                if "/Against_the_Storm/" not in href or "List_of" in href or "Species" in href:
                    continue
                title = a.get_text(strip=True)
                if not title or len(title) > 60:
                    continue
                if re.search(r"^(List|Category|File|Special|Template):", title, re.I):
                    continue
                building_name = title
                break
            if not building_name:
                continue
            s = slug(building_name)
            if s in seen_slugs:
                continue
            seen_slugs.add(s)
            img = tr.find("img", src=True) or tr.find("img", {"data-src": True})
            src = (img.get("src") or (img.get("data-src") if img else None)) if img else None
            if not src:
                continue
            url = resolve_image_url(src, IMAGE_WIDTH)
            out = blueprints_dir / f"{s}.png"
            print(f"  [building] {building_name} -> {out.name}")
            if not dry_run and url:
                if download_file(sess, url, out, timeout):
                    count += 1
            elif dry_run:
                count += 1
    return count


def scrape_species(sess: requests.Session, templates_dir: Path, dry_run: bool, timeout: int = 25) -> int:
    """从 Species 页或 List 页解析五种族图标"""
    species_dir = templates_dir / "species"
    if not dry_run:
        species_dir.mkdir(parents=True, exist_ok=True)

    try:
        html = fetch_html(sess, SPECIES_PAGE, timeout=timeout)
    except Exception as e:
        print(f"  [species] Skip {SPECIES_PAGE}: {e}", file=sys.stderr)
        return 0

    soup = BeautifulSoup(html, "html.parser")
    known = {"Human", "Beaver", "Harpy", "Lizard", "Fox"}
    count = 0
    for table in soup.find_all("table"):
        for tr in table.find_all("tr"):
            name = None
            for a in tr.find_all("a", href=re.compile(r"Against_the_Storm/(Human|Beaver|Harpy|Lizard|Fox)$")):
                name = a.get_text(strip=True) or a.get("href", "").split("/")[-1]
                break
            if not name or name not in known:
                continue
            img = tr.find("img", src=True) or tr.find("img", {"data-src": True})
            src = (img.get("src") or img.get("data-src")) if img else None
            if not src:
                continue
            url = resolve_image_url(src, IMAGE_WIDTH)
            fname = f"{name.lower()}.png"
            out = species_dir / fname
            print(f"  [species] {name} -> {out.name}")
            if not dry_run and url:
                if download_file(sess, url, out, timeout):
                    count += 1
            elif dry_run:
                count += 1
    return count


def main():
    parser = argparse.ArgumentParser(description="Download template images from Hooded Horse official wiki")
    parser.add_argument(
        "--templates-dir",
        type=str,
        default="backend/app/data/templates",
        help="Templates root directory",
    )
    parser.add_argument("--dry-run", action="store_true", help="Only print what would be downloaded")
    parser.add_argument("--timeout", type=int, default=25, help="Request timeout in seconds (default 25)")
    args = parser.parse_args()

    root = Path(__file__).resolve().parent.parent
    templates_dir = root / args.templates_dir
    print(f"Official Wiki: {BASE_URL}")
    print(f"Templates dir: {templates_dir}\n")

    sess = session()
    total = 0
    try:
        print("Buildings (List of Buildings):")
        total += scrape_buildings(sess, templates_dir, args.dry_run, args.timeout)
        print("\nSpecies:")
        total += scrape_species(sess, templates_dir, args.dry_run, args.timeout)
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"\nDone. Total: {total} (run normalize_template_images.py after)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
