#!/usr/bin/env python3
"""
从 Fandom Wiki 分类页抓取每栋建筑的 Cost（inputs）、Produces/Goods Produced（outputs）、
Workers（种族偏好），输出 building_details.json，供 build_ats_blueprints_data.py 使用。

数据来源（与 scrape_ats_wiki 一致）：
- https://against-the-storm.fandom.com/wiki/Camps  （Goods Produced, Cost, Workers）
- https://against-the-storm.fandom.com/wiki/Food_Production （Produces, Cost）
- https://against-the-storm.fandom.com/wiki/City_Buildings
- https://against-the-storm.fandom.com/wiki/Industry

用法：
  pip install -r scripts/requirements-scraper.txt
  python scripts/scrape_building_details.py [--out-dir DIR] [--ats-wiki DIR]
"""
import argparse
import json
import re
import sys
from pathlib import Path

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://against-the-storm.fandom.com"
USER_AGENT = "ATS-Wiki-Scraper/1.0 (data collection for game assistant)"
SPECIES_NAMES = {"Human", "Beaver", "Harpy", "Lizard", "Fox"}


def session():
    s = requests.Session()
    s.headers.update({"User-Agent": USER_AGENT})
    return s


def fetch_html(sess: requests.Session, path: str) -> str:
    r = sess.get(BASE_URL + path, timeout=30)
    r.raise_for_status()
    return r.text


def all_goods_from_json(ats_wiki_dir: Path) -> list:
    """从 goods.json 得到所有物资名（用于解析 Cost/Produces 时匹配）"""
    path = ats_wiki_dir / "goods.json"
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    names = []
    for v in data.values() if isinstance(data, dict) else []:
        if isinstance(v, list):
            names.extend(v)
    return sorted(names, key=len, reverse=True)  # 长名称优先匹配


def parse_cost_to_inputs(cost_text: str, known_goods: list) -> dict:
    """将 Cost 单元格文本解析为 {resource: amount}。例如 '2 Planks\\n2 Fabric' -> {Planks: 2, Fabric: 2}"""
    if not cost_text or cost_text.strip().lower() in ("none", "n/a", "-", ""):
        return {}
    inputs = {}
    # 先按换行、逗号、分号拆
    parts = re.split(r"[\n,;]+", cost_text)
    for part in parts:
        part = part.strip()
        if not part:
            continue
        # 匹配 "数字 物资名"（物资名可能多词，如 Copper Bar）
        m = re.match(r"^(\d+)\s+(.+)$", part.strip())
        if m:
            amount = int(m.group(1))
            rest = m.group(2).strip()
            # 匹配已知物资名（长优先）
            for g in known_goods:
                if rest == g or rest.startswith(g + " ") or rest.endswith(" " + g):
                    name = g
                    break
                # 单复数：Brick -> Bricks
                if rest.rstrip("s") == g or rest == g + "s":
                    name = g
                    break
            else:
                name = rest.replace(" ", "") if rest else ""
                if not name:
                    continue
                # 尝试用首词或常见名
                for g in known_goods:
                    if g in rest or rest in g:
                        name = g
                        break
            if name:
                inputs[name] = inputs.get(name, 0) + amount
    # 整段再扫一次 "5 Planks 2 Bricks" 这种无换行
    if not inputs and cost_text:
        for g in known_goods:
            pat = re.compile(r"(\d+)\s*" + re.escape(g) + r"(?:\s|$)", re.I)
            for m in pat.finditer(cost_text):
                inputs[g] = inputs.get(g, 0) + int(m.group(1))
    return inputs


def parse_produces_to_outputs(produces_text: str, known_goods: list) -> dict:
    """将 Produces / Goods Produced 解析为 {good: amount}。例如 'Clay (★★)\\nReed (★★)' -> {Clay: 1, Reed: 1}"""
    if not produces_text or produces_text.strip().lower() in ("n/a", "-", ""):
        return {}
    outputs = {}
    # 去掉 ★ 和括号，按换行或逗号拆
    clean = re.sub(r"\s*\([★\s*]+\)\s*", " ", produces_text)
    parts = re.split(r"[\n,;]+", clean)
    for part in parts:
        part = part.strip()
        if not part:
            continue
        # 可能带数字前缀 "10 Wood"
        m = re.match(r"^(\d+)\s+(.+)$", part)
        if m:
            amount = int(m.group(1))
            rest = m.group(2).strip()
        else:
            amount = 1
            rest = part
        for g in known_goods:
            if rest == g or rest.startswith(g + " ") or rest.endswith(" " + g):
                outputs[g] = outputs.get(g, 0) + amount
                break
        else:
            # 无匹配时用清理后的词（首词或整段）
            w = re.sub(r"\s+", " ", rest).strip()
            if w and w not in ("?", "None"):
                outputs[w] = outputs.get(w, 0) + amount
    return outputs


def parse_workers_to_species(workers_text: str) -> list:
    """Workers 列：若包含种族名则视为该建筑偏好该种族；仅 Any 则返回空（表示全部）"""
    if not workers_text:
        return []
    seen = set()
    lower = workers_text.lower()
    for s in SPECIES_NAMES:
        base = s.lower()
        # Beaver/Beavers, Human/Humans, Harpy/Harpies, Lizard/Lizards, Fox/Foxes
        if base in lower or (base + "s") in lower or (base.rstrip("y") + "ies") in lower:
            seen.add(s)
    if not seen:
        return []
    return sorted(seen)


def scrape_camps(sess: requests.Session, known_goods: list) -> dict:
    """Camps 页：表头 Icon, Name, Goods Produced, Cost, Movable, Workers"""
    html = fetch_html(sess, "/wiki/Camps")
    soup = BeautifulSoup(html, "html.parser")
    out = {}
    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        if len(rows) < 2:
            continue
        headers = [th.get_text(strip=True).lower() for th in rows[0].find_all(["th", "td"])]
        name_i = cost_i = prod_i = workers_i = None
        for i, h in enumerate(headers):
            if "name" in h:
                name_i = i
            if "cost" in h:
                cost_i = i
            if "good" in h or "produc" in h:
                prod_i = i
            if "worker" in h:
                workers_i = i
        if name_i is None:
            continue
        for tr in rows[1:]:
            cells = tr.find_all(["td", "th"])
            if max(name_i, cost_i or 0, prod_i or 0, workers_i or 0) >= len(cells):
                continue
            name_cell = cells[name_i]
            a = name_cell.find("a", href=re.compile(r"^/wiki/"))
            name = (a.get_text(strip=True) if a else name_cell.get_text(strip=True)) or ""
            if not name:
                continue
            cost_text = cells[cost_i].get_text(separator="\n", strip=True) if cost_i is not None and cost_i < len(cells) else ""
            prod_text = cells[prod_i].get_text(separator="\n", strip=True) if prod_i is not None and prod_i < len(cells) else ""
            workers_text = cells[workers_i].get_text(separator="\n", strip=True) if workers_i is not None and workers_i < len(cells) else ""
            inputs = parse_cost_to_inputs(cost_text, known_goods)
            outputs = parse_produces_to_outputs(prod_text, known_goods)
            species = parse_workers_to_species(workers_text)
            out[name] = {"inputs": inputs, "outputs": outputs, "species_preferences": species}
    return out


def scrape_food_production(sess: requests.Session, known_goods: list) -> dict:
    """Food_Production 页：多个表，列名 Name, Produces, Cost 或 Produces, Staff, Specialty, Cost"""
    html = fetch_html(sess, "/wiki/Food_Production")
    soup = BeautifulSoup(html, "html.parser")
    out = {}
    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        if len(rows) < 2:
            continue
        headers = [th.get_text(strip=True).lower() for th in rows[0].find_all(["th", "td"])]
        name_i = cost_i = prod_i = None
        for i, h in enumerate(headers):
            if "name" in h:
                name_i = i
            if "cost" in h:
                cost_i = i
            if "produc" in h:
                prod_i = i
        if name_i is None:
            continue
        for tr in rows[1:]:
            cells = tr.find_all(["td", "th"])
            if name_i >= len(cells):
                continue
            name_cell = cells[name_i]
            a = name_cell.find("a", href=re.compile(r"^/wiki/"))
            name = (a.get_text(strip=True) if a else name_cell.get_text(strip=True)) or ""
            if not name:
                continue
            cost_text = cells[cost_i].get_text(separator="\n", strip=True) if cost_i is not None and cost_i < len(cells) else ""
            prod_text = cells[prod_i].get_text(separator="\n", strip=True) if prod_i is not None and prod_i < len(cells) else ""
            inputs = parse_cost_to_inputs(cost_text, known_goods)
            outputs = parse_produces_to_outputs(prod_text, known_goods)
            out[name] = {"inputs": inputs, "outputs": outputs, "species_preferences": []}
    return out


def scrape_city_buildings(sess: requests.Session, known_goods: list) -> dict:
    html = fetch_html(sess, "/wiki/City_Buildings")
    soup = BeautifulSoup(html, "html.parser")
    out = {}
    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        if len(rows) < 2:
            continue
        headers = [th.get_text(strip=True).lower() for th in rows[0].find_all(["th", "td"])]
        name_i = cost_i = prod_i = workers_i = None
        for i, h in enumerate(headers):
            if "name" in h:
                name_i = i
            if "cost" in h:
                cost_i = i
            if "produc" in h or "good" in h:
                prod_i = i
            if "worker" in h:
                workers_i = i
        if name_i is None:
            continue
        for tr in rows[1:]:
            cells = tr.find_all(["td", "th"])
            if name_i >= len(cells):
                continue
            name_cell = cells[name_i]
            a = name_cell.find("a", href=re.compile(r"^/wiki/"))
            name = (a.get_text(strip=True) if a else name_cell.get_text(strip=True)) or ""
            if not name:
                continue
            cost_text = cells[cost_i].get_text(separator="\n", strip=True) if cost_i is not None and cost_i < len(cells) else ""
            prod_text = cells[prod_i].get_text(separator="\n", strip=True) if prod_i is not None and prod_i < len(cells) else ""
            workers_text = cells[workers_i].get_text(separator="\n", strip=True) if workers_i is not None and workers_i < len(cells) else ""
            inputs = parse_cost_to_inputs(cost_text, known_goods)
            outputs = parse_produces_to_outputs(prod_text, known_goods)
            species = parse_workers_to_species(workers_text)
            out[name] = {"inputs": inputs, "outputs": outputs, "species_preferences": species}
    return out


def scrape_industry(sess: requests.Session, known_goods: list) -> dict:
    html = fetch_html(sess, "/wiki/Industry")
    soup = BeautifulSoup(html, "html.parser")
    out = {}
    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        if len(rows) < 2:
            continue
        headers = [th.get_text(strip=True).lower() for th in rows[0].find_all(["th", "td"])]
        name_i = cost_i = prod_i = workers_i = None
        for i, h in enumerate(headers):
            if "name" in h:
                name_i = i
            if "cost" in h:
                cost_i = i
            if "produc" in h or "good" in h:
                prod_i = i
            if "worker" in h:
                workers_i = i
        if name_i is None:
            continue
        for tr in rows[1:]:
            cells = tr.find_all(["td", "th"])
            if name_i >= len(cells):
                continue
            name_cell = cells[name_i]
            a = name_cell.find("a", href=re.compile(r"^/wiki/"))
            name = (a.get_text(strip=True) if a else name_cell.get_text(strip=True)) or ""
            if not name:
                continue
            cost_text = cells[cost_i].get_text(separator="\n", strip=True) if cost_i is not None and cost_i < len(cells) else ""
            prod_text = cells[prod_i].get_text(separator="\n", strip=True) if prod_i is not None and prod_i < len(cells) else ""
            workers_text = cells[workers_i].get_text(separator="\n", strip=True) if workers_i is not None and workers_i < len(cells) else ""
            inputs = parse_cost_to_inputs(cost_text, known_goods)
            outputs = parse_produces_to_outputs(prod_text, known_goods)
            species = parse_workers_to_species(workers_text)
            out[name] = {"inputs": inputs, "outputs": outputs, "species_preferences": species}
    return out


def main():
    parser = argparse.ArgumentParser(description="Scrape Fandom for building Cost/Produces/Workers")
    parser.add_argument("--out-dir", type=str, default="backend/app/data/ats_wiki", help="Output directory")
    parser.add_argument("--ats-wiki", type=str, default="backend/app/data/ats_wiki", help="ats_wiki dir for goods.json")
    args = parser.parse_args()

    root = Path(__file__).resolve().parent.parent
    ats_wiki = root / args.ats_wiki
    out_dir = root / args.out_dir
    known_goods = all_goods_from_json(ats_wiki)

    sess = session()
    all_details = {}

    print("Scraping Camps...")
    all_details.update(scrape_camps(sess, known_goods))
    print("Scraping Food_Production...")
    all_details.update(scrape_food_production(sess, known_goods))
    print("Scraping City_Buildings...")
    all_details.update(scrape_city_buildings(sess, known_goods))
    print("Scraping Industry...")
    all_details.update(scrape_industry(sess, known_goods))

    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "building_details.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(all_details, f, indent=2, ensure_ascii=False)
    print(f"Wrote {len(all_details)} building details to {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
