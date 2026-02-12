#!/usr/bin/env python3
"""
从 Fandom Wiki 抓取配方：每栋建筑能造什么、所需资源及数量、制作时间、评级。

数据来源：
1) https://against-the-storm.fandom.com/wiki/Recipes 总表
2) 各建筑子页（如 /wiki/Bakery）的 Recipes 表：Produced | Product | Grade | Production Time | Ingredients

输出：
- ats_wiki/recipes.json：完整配方列表（含 building, product, output_amount, inputs, duration_seconds, rating）
- ats_wiki/recipes_by_building.json：按建筑名分组的配方

用法：
  pip install -r scripts/requirements-scraper.txt
  python scripts/scrape_recipes.py [--out-dir DIR] [--ats-wiki DIR] [--skip-pages]
"""
import argparse
import json
import re
import sys
import time
from pathlib import Path
from collections import defaultdict
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://against-the-storm.fandom.com"
USER_AGENT = "ATS-Wiki-Scraper/1.0 (data collection for game assistant)"


def session():
    s = requests.Session()
    s.headers.update({"User-Agent": USER_AGENT})
    return s


def fetch_html(sess: requests.Session, path: str) -> str:
    r = sess.get(BASE_URL + path, timeout=30)
    r.raise_for_status()
    return r.text


def all_goods_from_json(ats_wiki_dir: Path) -> list:
    path = ats_wiki_dir / "goods.json"
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    names = []
    for v in data.values() if isinstance(data, dict) else []:
        if isinstance(v, list):
            names.extend(v)
    return sorted(names, key=len, reverse=True)


def parse_input_cell(text: str, known_goods: list) -> dict:
    """
    解析 Input 1/Input 2 单元格，如 "3 Clay 3 Stone" 或 "8 Wood 2 Planks"。
    Wiki 说明：同一单元格内多种材料表示「只需其一」，这里合并为所需集合（取第一种作为主需求便于展示）。
    """
    if not text or not text.strip():
        return {}
    # 去掉 * 和多余空白，统一空格
    text = re.sub(r"\*", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    inputs = {}
    # 用已知物资名从长到短匹配，避免 "Copper Bar" 被拆成 "Copper"
    remaining = text
    for g in known_goods:
        # 匹配 "数字 g" 或 "数字 g "
        pat = re.compile(r"(\d+)\s*" + re.escape(g) + r"(?:\s|$)", re.I)
        for m in pat.finditer(remaining):
            inputs[g] = inputs.get(g, 0) + int(m.group(1))
    if not inputs and remaining:
        # 回退：(\d+)\s+(\w+(?:\s+\w+)?)
        for m in re.finditer(r"(\d+)\s+([A-Za-z][A-Za-z\s]*?)(?=\s*\d|$)", remaining):
            amount, name = int(m.group(1)), m.group(2).strip()
            if name:
                inputs[name] = inputs.get(name, 0) + amount
    return inputs


def parse_duration(s: str):
    """解析时长：24 -> 24；00:06 -> 6（分钟）；空 -> None"""
    if not s or not s.strip():
        return None
    s = s.strip()
    if ":" in s:
        parts = s.split(":")
        if len(parts) == 2:
            try:
                return int(parts[0]) * 60 + int(parts[1])
            except ValueError:
                pass
    try:
        return int(re.sub(r"\D", "", s) or 0) or None
    except ValueError:
        return None


def parse_rating(s: str) -> str:
    """保留星级原文，如 ★★★、★★、★"""
    if not s:
        return ""
    return s.strip()


def scrape_recipes(sess: requests.Session, known_goods: list):
    """
    抓取 Recipes 页表格，返回 (flat_list, by_building)。
    表格可能：Product 列为空时表示同一产品、不同建筑。
    """
    html = fetch_html(sess, "/wiki/Recipes")
    soup = BeautifulSoup(html, "html.parser")
    flat = []
    by_building = defaultdict(list)
    current_product = None

    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        if len(rows) < 2:
            continue
        headers = [th.get_text(strip=True) for th in rows[0].find_all(["th", "td"])]
        if "Product" not in str(headers[0]) or "Production Building" not in str(headers):
            continue
        for tr in rows[1:]:
            cells = tr.find_all(["td", "th"])
            if len(cells) < 4:
                continue
            # 表可能 6 列 (Product, Building, Rating, Duration, Inp1, Inp2) 或 5 列（无 Product，即续行）
            is_continuation = len(cells) == 5 and parse_rating(cells[1].get_text(strip=True)) in ("★", "★★", "★★★")
            if is_continuation:
                product = ""
                building = cells[0].get_text(strip=True)
                rating = parse_rating(cells[1].get_text(strip=True))
                duration_raw = cells[2].get_text(strip=True) if len(cells) > 2 else ""
                inp1 = cells[3].get_text(separator=" ", strip=True) if len(cells) > 3 else ""
                inp2 = cells[4].get_text(separator=" ", strip=True) if len(cells) > 4 else ""
            else:
                product = cells[0].get_text(strip=True) if len(cells) > 0 else ""
                building = cells[1].get_text(strip=True) if len(cells) > 1 else ""
                rating = parse_rating(cells[2].get_text(strip=True) if len(cells) > 2 else "")
                duration_raw = cells[3].get_text(strip=True) if len(cells) > 3 else ""
                inp1 = cells[4].get_text(separator=" ", strip=True) if len(cells) > 4 else ""
                inp2 = cells[5].get_text(separator=" ", strip=True) if len(cells) > 5 else ""

            if product:
                current_product = product
            if not current_product:
                continue
            if not building or building in ("★", "★★", "★★★"):
                continue
            duration = parse_duration(duration_raw)
            inputs1 = parse_input_cell(inp1, known_goods)
            inputs2 = parse_input_cell(inp2, known_goods)
            # 合并 Input 1 与 Input 2（通常 Input 2 是同一配方的额外需求）
            merged = dict(inputs1)
            for k, v in inputs2.items():
                merged[k] = merged.get(k, 0) + v

            entry = {
                "product": current_product,
                "output_amount": 1,
                "building": building,
                "rating": rating,
                "duration_seconds": duration,
                "inputs": merged,
            }
            flat.append(entry)
            by_building[building].append(entry)
        break  # 只处理第一个符合条件的表
    return flat, dict(by_building)


def building_name_to_wiki_path(name: str) -> str:
    """建筑名转 Wiki 路径：Brick Oven -> Brick_Oven, Woodcutters' Camp -> Woodcutters'_Camp"""
    # Fandom: 空格用 _，撇号保留
    slug = name.replace(" ", "_")
    return "/wiki/" + quote(slug, safe="")


def parse_produced_cell(text: str) -> tuple:
    """解析 Produced 列，如 '10 Biscuits' -> (10, 'Biscuits')"""
    if not text or not text.strip():
        return (1, "")
    text = re.sub(r"\s+", " ", text).strip()
    m = re.match(r"^(\d+)\s+(.+)$", text)
    if m:
        return (int(m.group(1)), m.group(2).strip())
    return (1, text)


def scrape_building_page_recipes(
    sess: requests.Session,
    building_name: str,
    known_goods: list,
    delay_seconds: float = 0.4,
) -> list:
    """
    抓取单栋建筑子页的 Recipes 表。表头：Produced | Product | Grade | Production Time | Ingredients [1] | [2]
    返回该建筑的配方列表。
    """
    path = building_name_to_wiki_path(building_name)
    time.sleep(delay_seconds)
    try:
        html = fetch_html(sess, path)
    except Exception:
        return []
    soup = BeautifulSoup(html, "html.parser")
    recipes = []
    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        if len(rows) < 2:
            continue
        headers = [th.get_text(strip=True) for th in rows[0].find_all(["th", "td"])]
        if "Produced" not in str(headers) and "Product" not in str(headers) and "Grade" not in str(headers):
            continue
        prod_idx = next((i for i, h in enumerate(headers) if "Produced" in h), next((i for i, h in enumerate(headers) if "Product" in h), 0))
        grade_idx = next((i for i, h in enumerate(headers) if "Grade" in h or "Rating" in h), 1)
        time_idx = next((i for i, h in enumerate(headers) if "Time" in h or "Duration" in h), 2)
        ing_indices = [i for i, h in enumerate(headers) if "Ingredient" in h]
        ing_idx = ing_indices[0] if ing_indices else 3
        ing2_idx = ing_indices[1] if len(ing_indices) > 1 else 4
        max_idx = max(prod_idx, grade_idx, time_idx, ing_idx, ing2_idx)
        for tr in rows[1:]:
            cells = tr.find_all(["td", "th"])
            if max_idx >= len(cells):
                continue
            produced_text = cells[prod_idx].get_text(separator=" ", strip=True)
            output_amount, product = parse_produced_cell(produced_text)
            if not product:
                continue
            rating = parse_rating(cells[grade_idx].get_text(strip=True) if grade_idx < len(cells) else "")
            duration_raw = cells[time_idx].get_text(strip=True) if time_idx < len(cells) else ""
            inp1 = cells[ing_idx].get_text(separator=" ", strip=True) if ing_idx < len(cells) else ""
            inp2 = cells[ing2_idx].get_text(separator=" ", strip=True) if ing2_idx < len(cells) else ""
            # Ingredients 可能含 "8 Flour" 和 "3 Herbs OR 3 Berries" -> 取第一种选项
            inp1 = re.sub(r"\s+OR\s+\d+\s+", " ", inp1)
            inp2 = re.sub(r"\s+OR\s+\d+\s+", " ", inp2)
            merged = parse_input_cell(inp1, known_goods)
            for k, v in parse_input_cell(inp2, known_goods).items():
                merged[k] = merged.get(k, 0) + v
            duration = parse_duration(duration_raw)
            recipes.append({
                "product": product,
                "output_amount": output_amount,
                "building": building_name,
                "rating": rating,
                "duration_seconds": duration,
                "inputs": merged,
            })
        break
    return recipes


def get_building_names_to_fetch(ats_wiki_dir: Path, templates_dir: Path) -> list:
    """从 buildings.json 与 templates 取有模板的建筑名列表（用于抓子页）"""
    buildings_path = ats_wiki_dir / "buildings.json"
    if not buildings_path.exists():
        return []
    data = json.loads(buildings_path.read_text(encoding="utf-8"))
    template_stems = set()
    if templates_dir.exists():
        for f in (templates_dir / "blueprints").glob("*.png"):
            template_stems.add(f.stem)
    if not template_stems:
        return []
    def slug(n):
        return re.sub(r"[^a-z0-9_]", "", re.sub(r"[\s']+", "_", n).lower())
    names = []
    for cat, lst in data.items():
        if not isinstance(lst, list):
            continue
        for name in lst:
            if name and isinstance(name, str) and slug(name) in template_stems and name not in names:
                names.append(name)
    return names


def main():
    parser = argparse.ArgumentParser(description="Scrape Fandom Recipes and per-building recipe tables")
    parser.add_argument("--out-dir", type=str, default="backend/app/data/ats_wiki")
    parser.add_argument("--ats-wiki", type=str, default="backend/app/data/ats_wiki")
    parser.add_argument("--skip-pages", action="store_true", help="Only scrape Recipes page, skip per-building pages")
    args = parser.parse_args()

    root = Path(__file__).resolve().parent.parent
    ats_wiki = root / args.ats_wiki
    out_dir = root / args.out_dir
    templates_dir = root / "backend/app/data/templates"
    known_goods = all_goods_from_json(ats_wiki)

    sess = session()
    flat, by_building = scrape_recipes(sess, known_goods)

    if not args.skip_pages:
        building_names = get_building_names_to_fetch(ats_wiki, templates_dir)
        print(f"Fetching recipe tables for {len(building_names)} buildings...")
        for name in building_names:
            page_recipes = scrape_building_page_recipes(sess, name, known_goods)
            if page_recipes:
                for rec in page_recipes:
                    flat.append(rec)
                    if name not in by_building:
                        by_building[name] = []
                    by_building[name].append(rec)
                print(f"  {name}: {len(page_recipes)} recipes")

    out_dir.mkdir(parents=True, exist_ok=True)
    recipes_path = out_dir / "recipes.json"
    by_building_path = out_dir / "recipes_by_building.json"

    with open(recipes_path, "w", encoding="utf-8") as f:
        json.dump(flat, f, indent=2, ensure_ascii=False)
    with open(by_building_path, "w", encoding="utf-8") as f:
        json.dump(dict(by_building), f, indent=2, ensure_ascii=False)

    print(f"Wrote {len(flat)} recipes to {recipes_path}")
    print(f"Wrote {len(by_building)} buildings to {by_building_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
