#!/usr/bin/env python3
"""
从 Against the Storm Fandom Wiki 抓取基础数据：
- Goods（物资，含分类）
- Buildings（建筑，按分类）
- Species（种族）
- Cornerstone（基石）

数据来源：
- https://against-the-storm.fandom.com/wiki/Goods
- https://against-the-storm.fandom.com/wiki/Buildings 及子页（Camps, Food_Production 等）
- https://against-the-storm.fandom.com/wiki/Species
- https://against-the-storm.fandom.com/wiki/Cornerstone

用法：
  pip install -r scripts/requirements-scraper.txt
  python scripts/scrape_ats_wiki.py [--out-dir DIR] [--verify]
"""
import argparse
import json
import re
import sys
from pathlib import Path

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://against-the-storm.fandom.com"
API_URL = f"{BASE_URL}/api.php"
USER_AGENT = "ATS-Wiki-Scraper/1.0 (data collection for game assistant)"


def session():
    s = requests.Session()
    s.headers.update({"User-Agent": USER_AGENT})
    return s


def api_parse(sess: requests.Session, page: str) -> str:
    """获取 MediaWiki 解析后的 HTML 内容"""
    r = sess.get(
        API_URL,
        params={
            "action": "parse",
            "page": page,
            "format": "json",
            "prop": "text",
        },
        timeout=30,
    )
    r.raise_for_status()
    data = r.json()
    if "error" in data:
        raise RuntimeError(f"API error: {data['error']}")
    return data["parse"]["text"]["*"]


def fetch_html(sess: requests.Session, path: str) -> str:
    """直接获取页面 HTML"""
    r = sess.get(BASE_URL + path, timeout=30)
    r.raise_for_status()
    return r.text


# ---------- Goods ----------


def scrape_goods(sess: requests.Session) -> dict:
    """
    抓取 Goods 页面：按分类列出物资名称。
    页面结构：ul > li（分类）> span/文本 + ul > li > a[href=/wiki/XXX]（物资名）
    """
    html = api_parse(sess, "Goods")
    soup = BeautifulSoup(html, "html.parser")
    result = {}
    # 只处理 mw-parser-output 下的主列表，避免抓到边栏等
    root = soup.find("div", class_=re.compile("mw-parser-output"))
    if not root:
        root = soup
    for li in root.find_all("li", recursive=True):
        nested_ul = li.find("ul")
        if not nested_ul:
            continue
        # 分类名：取 li 下第一个 span / a 或短文本（在 ul 之前），且长度合理
        category = ""
        for node in li.children:
            if node.name == "ul":
                break
            if hasattr(node, "get_text"):
                t = node.get_text(strip=True)
                if t and len(t) < 60 and "page does not exist" not in str(getattr(node, "get", lambda _: "")("title", "")):
                    category = t
                    break
            else:
                # 文本节点（str 或 NavigableString）
                t = (node.strip() if hasattr(node, "strip") else str(node).strip()) or ""
                if t and len(t) < 60:
                    category = t
                    break
        if not category:
            first_line = li.get_text(strip=True).split("\n")[0].strip()
            category = first_line[:60] if first_line else "Uncategorized"
        # 若被拼成 "FoodBerries..." 则只保留首词（最后一个大写开头前的部分）
        if category and not category.endswith(" ") and len(category) > 20:
            for i, c in enumerate(category):
                if i > 0 and c.isupper() and category[i - 1].isalpha():
                    category = category[:i]
                    break
        items = []
        for a in nested_ul.find_all("a", href=re.compile(r"^/wiki/[^:]+$")):
            if "File:" in (a.get("href") or ""):
                continue
            name = a.get_text(strip=True)
            if name and name not in items:
                items.append(name)
        if category and items:
            result[category] = items
    return result


# ---------- Buildings ----------


BUILDING_CATEGORY_PAGES = [
    ("Camps", "/wiki/Camps"),
    ("Food_Production", "/wiki/Food_Production"),
    ("Housing", "/wiki/Housing"),
    ("Industry", "/wiki/Industry"),
    ("City_Buildings", "/wiki/City_Buildings"),
    ("Decorations", "/wiki/Decorations"),
    ("Roads", "/wiki/Roads"),
]


def scrape_buildings(sess: requests.Session) -> dict:
    """
    抓取 Buildings 各分类子页，从表格中提取建筑名称。
    表格列：Icon, Name, (Goods Produced, Cost, ...)
    """
    result = {}
    for category, path in BUILDING_CATEGORY_PAGES:
        try:
            html = fetch_html(sess, path)
        except Exception as e:
            print(f"  [Buildings] 跳过 {category}: {e}", file=sys.stderr)
            result[category] = []
            continue
        soup = BeautifulSoup(html, "html.parser")
        buildings = []
        for table in soup.find_all("table", class_=re.compile("wikitable|article-table|fandom-table|sortable")):
            rows = table.find_all("tr")
            if not rows:
                continue
            headers = [th.get_text(strip=True) for th in rows[0].find_all(["th", "td"])]
            name_idx = None
            for i, h in enumerate(headers):
                if h and "name" in h.lower():
                    name_idx = i
                    break
            if name_idx is None:
                name_idx = 1
            for tr in rows[1:]:
                cells = tr.find_all(["td", "th"])
                if len(cells) <= name_idx:
                    continue
                name_cell = cells[name_idx]
                a = name_cell.find("a", href=re.compile(r"^/wiki/"))
                if a:
                    name = a.get_text(strip=True)
                    if name and name not in buildings:
                        buildings.append(name)
                else:
                    name = name_cell.get_text(strip=True)
                    if name and name not in buildings:
                        buildings.append(name)
        result[category] = buildings
    return result


# ---------- Species ----------


def scrape_species(sess: requests.Session) -> dict:
    """
    抓取 Species 页面：种族表（名称、Base Resolve 等）和 Needs 表。
    """
    html = api_parse(sess, "Species")
    soup = BeautifulSoup(html, "html.parser")
    species_list = []
    needs_data = []
    tables = soup.find_all("table")
    for table in tables:
        rows = table.find_all("tr")
        if not rows:
            continue
        headers = [th.get_text(strip=True) for th in rows[0].find_all(["th", "td"])]
        if not headers:
            continue
        # 第一个表：Species, Base Resolve, Break Interval, ...
        if "Species" in headers[0] or "Base Resolve" in str(headers):
            for tr in rows[1:]:
                cells = tr.find_all(["td", "th"])
                if not cells:
                    continue
                name_cell = cells[0]
                a = name_cell.find("a", href=re.compile(r"^/wiki/"))
                name = (a.get_text(strip=True) if a else name_cell.get_text(strip=True)) or ""
                if not name or name == "Species":
                    continue
                row = {"name": name}
                for i, h in enumerate(headers[1:], 1):
                    if i < len(cells):
                        row[h] = cells[i].get_text(strip=True)
                species_list.append(row)
        # Needs 表：第一列是需求名，后面是各种族数值
        elif "Needs" in str(headers[0]) or (len(headers) >= 5 and any("Beaver" in str(h) or "Human" in str(h) for h in headers)):
            species_cols = headers[1:6]  # Beaver, Harpy, Human, Lizard, Fox
            for tr in rows[1:]:
                cells = tr.find_all(["td", "th"])
                if len(cells) < 2:
                    continue
                need_name = cells[0].get_text(strip=True)
                if not need_name or need_name == "Needs":
                    continue
                values = {}
                for i, col in enumerate(species_cols):
                    if i + 1 < len(cells):
                        values[col] = cells[i + 1].get_text(strip=True)
                needs_data.append({"need": need_name, "species_values": values})
    return {"species": species_list, "needs": needs_data}


# ---------- Cornerstone ----------


def scrape_cornerstones(sess: requests.Session) -> list:
    """
    抓取 Cornerstone 页面：表格列 Name, Effect, Rarity。
    使用 API 获取解析后 HTML，再解析表格。
    """
    html = api_parse(sess, "Cornerstone")
    soup = BeautifulSoup(html, "html.parser")
    items = []
    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        if len(rows) < 2:
            continue
        headers = [th.get_text(strip=True) for th in rows[0].find_all(["th", "td"])]
        if "Name" not in headers and "Effect" not in headers:
            continue
        name_idx = next((i for i, h in enumerate(headers) if "name" in h.lower()), 0)
        effect_idx = next((i for i, h in enumerate(headers) if "effect" in h.lower()), 1)
        rarity_idx = next((i for i, h in enumerate(headers) if "rarity" in h.lower()), 2)
        for tr in rows[1:]:
            cells = tr.find_all(["td", "th"])
            if max(name_idx, effect_idx, rarity_idx) >= len(cells):
                continue
            name = cells[name_idx].get_text(strip=True)
            effect = cells[effect_idx].get_text(strip=True)
            rarity = cells[rarity_idx].get_text(strip=True)
            if name:
                items.append({"name": name, "effect": effect, "rarity": rarity})
    return items


# ---------- Main ----------


def main():
    parser = argparse.ArgumentParser(description="Scrape Against the Storm Wiki for base data")
    parser.add_argument("--out-dir", type=str, default="backend/app/data/ats_wiki", help="Output directory for JSON files")
    parser.add_argument("--verify", action="store_true", help="Only run scrapers and print counts, no write")
    args = parser.parse_args()

    sess = session()
    out_dir = Path(args.out_dir)
    if not args.verify:
        out_dir.mkdir(parents=True, exist_ok=True)

    print("Fetching Goods...")
    goods = scrape_goods(sess)
    total_goods = sum(len(v) for v in goods.values())
    print(f"  Goods: {total_goods} items in {len(goods)} categories: {list(goods.keys())}")

    print("Fetching Buildings...")
    buildings = scrape_buildings(sess)
    total_buildings = sum(len(v) for v in buildings.values())
    print(f"  Buildings: {total_buildings} in {len(buildings)} categories: {list(buildings.keys())}")

    print("Fetching Species...")
    species_data = scrape_species(sess)
    print(f"  Species: {len(species_data['species'])} races, {len(species_data['needs'])} needs rows")

    print("Fetching Cornerstones...")
    cornerstones = scrape_cornerstones(sess)
    print(f"  Cornerstones: {len(cornerstones)} items")

    if args.verify:
        print("\n[--verify] Skip writing files.")
        return 0

    (out_dir / "goods.json").write_text(json.dumps(goods, indent=2, ensure_ascii=False), encoding="utf-8")
    (out_dir / "buildings.json").write_text(json.dumps(buildings, indent=2, ensure_ascii=False), encoding="utf-8")
    (out_dir / "species.json").write_text(json.dumps(species_data, indent=2, ensure_ascii=False), encoding="utf-8")
    (out_dir / "cornerstones.json").write_text(json.dumps(cornerstones, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nWrote JSON to {out_dir.absolute()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
