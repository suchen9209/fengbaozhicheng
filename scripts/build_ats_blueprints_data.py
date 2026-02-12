#!/usr/bin/env python3
"""
根据 ats_wiki/buildings.json 与 templates/blueprints/*.png 生成符合 Blueprint 模型的
blueprints_data_ats.json，使推荐引擎能跑通（含 inputs/outputs/values/complexity/synergy）。

模板文件名即 slug；与 buildings 名 slug 一致则纳入。
"""
import json
import re
import sys
from pathlib import Path


def slug(s: str) -> str:
    s = re.sub(r"[\s']+", "_", s)
    s = re.sub(r"[^a-zA-Z0-9_]", "", s)
    return s.lower() or "unknown"


# ATS 五种族：逻辑层统一英文
ATS_SPECIES = ["Human", "Beaver", "Harpy", "Lizard", "Fox"]

# 按分类设定复杂度（1-5），便于推荐时有区分度
COMPLEXITY_BY_TYPE = {
    "Camps": 1,
    "Food_Production": 2,
    "Housing": 2,
    "Industry": 3,
    "City_Buildings": 2,
    "Decorations": 1,
    "Roads": 1,
}

# 建筑名 -> (food, fuel, resolve) 0-5，与游戏内价值倾向近似（无官方数据时按类型/名称推断）
def get_values(name: str, category: str) -> dict:
    n = name.lower()
    # 营地：偏燃料/决心
    if category == "Camps":
        return {"food": 0, "fuel": 3, "resolve": 2}
    # 食品生产：厨房/面包房等高食物价值
    if category == "Food_Production":
        if any(x in n for x in ("cookhouse", "bakery", "grill", "field kitchen")):
            return {"food": 4, "fuel": 1, "resolve": 1}
        if any(x in n for x in ("brewery", "distillery", "cellar")):
            return {"food": 1, "fuel": 0, "resolve": 4}
        if any(x in n for x in ("brick oven", "smokehouse")):
            return {"food": 2, "fuel": 4, "resolve": 0}
        if any(x in n for x in ("butcher", "granary")):
            return {"food": 3, "fuel": 1, "resolve": 0}
        # 农场、温室等
        return {"food": 3, "fuel": 0, "resolve": 1}
    # 城市/服务：偏决心
    if category == "City_Buildings":
        if any(x in n for x in ("bath", "tavern", "temple", "monastery")):
            return {"food": 0, "fuel": 1, "resolve": 4}
        return {"food": 0, "fuel": 0, "resolve": 3}
    if category == "Industry":
        return {"food": 0, "fuel": 2, "resolve": 2}
    return {"food": 2, "fuel": 2, "resolve": 1}


def main():
    root = Path(__file__).resolve().parent.parent
    ats_wiki = root / "backend/app/data/ats_wiki"
    templates_blueprints = root / "backend/app/data/templates/blueprints"
    out_path = root / "backend/app/data/blueprints_data_ats.json"

    if not ats_wiki.exists() or not templates_blueprints.exists():
        print("Missing ats_wiki or templates/blueprints", file=sys.stderr)
        return 1

    with open(ats_wiki / "buildings.json", "r", encoding="utf-8") as f:
        buildings_by_cat = json.load(f)

    template_slugs = {f.stem for f in templates_blueprints.glob("*.png")}

    # 收集 (building_name, type) 且 slug 在模板中的
    entries = []
    for category, names in buildings_by_cat.items():
        if not isinstance(names, list):
            continue
        for name in names:
            if not name or not isinstance(name, str):
                continue
            s = slug(name)
            if s in template_slugs:
                entries.append((name, category))

    # 去重（同一建筑可能出现在多分类）
    seen = set()
    unique = []
    for name, category in entries:
        if name in seen:
            continue
        seen.add(name)
        unique.append((name, category))

    # 从 Fandom 抓取的建筑详情（inputs/outputs/species_preferences），无则用占位
    building_details = {}
    details_path = ats_wiki / "building_details.json"
    if details_path.exists():
        try:
            building_details = json.loads(details_path.read_text(encoding="utf-8"))
        except Exception:
            pass

    # 为每栋建筑生成符合 Blueprint 的数据（优先用 building_details，否则占位）
    blueprints = []
    for name, category in unique:
        details = building_details.get(name, {})
        inputs = details.get("inputs")
        outputs = details.get("outputs")
        species_prefs = details.get("species_preferences")
        if not inputs or not isinstance(inputs, dict):
            if category == "Camps":
                inputs = {"Wood": 10, "Parts": 3}
            elif "Food" in category:
                inputs = {"Grain": 5, "Wood": 5}
            else:
                inputs = {"Planks": 5, "Parts": 2}
        if not outputs or not isinstance(outputs, dict):
            if category == "Camps":
                outputs = {"Wood": 20}
            elif "Food" in category:
                outputs = {"Flour": 8}
            else:
                outputs = {"Parts": 4}
        if not species_prefs:
            species_prefs = list(ATS_SPECIES)

        values = get_values(name, category)
        complexity = COMPLEXITY_BY_TYPE.get(category, 2)
        synergy = {"species_preferences": species_prefs, "biome_bonuses": {}}
        blueprints.append({
            "name": name,
            "name_en": name,
            "type": category,
            "dlc": "Base",
            "inputs": inputs,
            "outputs": outputs,
            "values": values,
            "complexity": complexity,
            "synergy": synergy,
            "description": f"ATS building: {name} ({category})"
        })

    out_data = {
        "version": "1.0.0",
        "last_updated": "2026-02-12",
        "source": "ats_wiki + templates",
        "blueprints": blueprints
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out_data, f, ensure_ascii=False, indent=2)
    print(f"Wrote {len(blueprints)} blueprints to {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
