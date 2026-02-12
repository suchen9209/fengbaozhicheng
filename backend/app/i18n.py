"""
中英文展示与归一化：内部逻辑一律英文，返回时按 lang 转为中文或保持英文。

说明：
- 英文以 Against the Storm Fandom Wiki 为准：https://against-the-storm.fandom.com/wiki/
- 该 Wiki 为纯英文，无站内中文。中文译名来自游戏官方本地化（《风暴之城》Steam/主机简中）
  及社区常用译名（如维基、攻略中的 人类/海狸/鸟身女妖/蜥蜴人/狐狸）。未在官方或社区
  查到的项保留英文展示。
"""
from typing import Dict, Optional

# 物种：英文以 Wiki 为准，中文以游戏/社区常用译名（人类、海狸、鸟身女妖、蜥蜴人、狐狸）
SPECIES_EN_TO_ZH: Dict[str, str] = {
    "Human": "人类",
    "Beaver": "海狸",
    "Harpy": "鸟身女妖",
    "Lizard": "蜥蜴人",
    "Fox": "狐狸",
}
SPECIES_ZH_TO_EN: Dict[str, str] = {v: k for k, v in SPECIES_EN_TO_ZH.items()}

# 资源：英文以 Wiki Goods 为准；中文为常见译名（游戏内可能不同），非 Fandom 提供
RESOURCES_EN_TO_ZH: Dict[str, str] = {
    "Wood": "木材",
    "Planks": "木板",
    "Parts": "零件",
    "Stone": "石料",
    "Clay": "黏土",
    "Grain": "谷物",
    "Flour": "面粉",
    "Herbs": "草药",
    "Coal": "煤炭",
    "Bricks": "砖块",
    "Fabric": "布料",
    "Reed": "芦苇",
    "Food": "食物",
    "Biscuits": "饼干",
    "Pie": "馅饼",
    "Meat": "肉类",
    "Vegetables": "蔬菜",
    "Berries": "浆果",
    "Mushrooms": "蘑菇",
    "Eggs": "蛋",
    "Jerky": "肉干",
    "Pickled Goods": "腌制品",
    "Skewers": "肉串",
    "Ale": "麦酒",
    "Wine": "葡萄酒",
    "Coats": "外套",
    "Scrolls": "卷轴",
    "Training Gear": "训练装备",
    "Incense": "熏香",
    "Cosmetics": "化妆品",
    "Barrels": "木桶",
    "Leather": "皮革",
    "Pottery": "陶器",
    "Resin": "树脂",
    "Plant Fiber": "植物纤维",
    "Pigment": "颜料",
    "Copper Ore": "铜矿",
    "Copper Bar": "铜锭",
    "Waterskins": "水袋",
    "Oil": "油",
    "Simple Tools": "简易工具",
    "Amber": "琥珀",
}
RESOURCES_ZH_TO_EN: Dict[str, str] = {v: k for k, v in RESOURCES_EN_TO_ZH.items()}

# 建筑名：英文以 Wiki Buildings 为准；中文暂无官方对照表时保留英文，待从游戏内或社区补充
# 以下为常见意译，非 Fandom 提供（Wiki 无中文）
BUILDINGS_EN_TO_ZH: Dict[str, str] = {
    "Clay Pit": "Clay Pit",
    "Forager's Camp": "Forager's Camp",
    "Harvester's Camp": "Harvester's Camp",
    "Herbalists' Camp": "Herbalists' Camp",
    "Stonecutters' Camp": "Stonecutters' Camp",
    "Trappers' Camp": "Trappers' Camp",
    "Woodcutters' Camp": "Woodcutters' Camp",
    "Greenhouse": "Greenhouse",
    "Herb Garden": "Herb Garden",
    "Homestead": "Homestead",
    "Plantation": "Plantation",
    "Ranch": "Ranch",
    "Small Farm": "Small Farm",
    "Bakery": "Bakery",
    "Brewery": "Brewery",
    "Brick Oven": "Brick Oven",
    "Butcher": "Butcher",
    "Cellar": "Cellar",
    "Cookhouse": "Cookhouse",
    "Distillery": "Distillery",
    "Field Kitchen": "Field Kitchen",
    "Granary": "Granary",
    "Grill": "Grill",
    "Smokehouse": "Smokehouse",
    "Bath House": "Bath House",
    "Clan Hall": "Clan Hall",
    "Explorer's Lodge": "Explorer's Lodge",
    "Guild House": "Guild House",
    "Monastery": "Monastery",
    "Tavern": "Tavern",
    "Temple": "Temple",
}
BUILDINGS_ZH_TO_EN: Dict[str, str] = {v: k for k, v in BUILDINGS_EN_TO_ZH.items()}


def species_to_display(species_en: str, lang: str) -> str:
    """内部物种（英文）-> 展示用（zh 返回中文，否则英文）"""
    if lang == "zh":
        return SPECIES_EN_TO_ZH.get(species_en, species_en)
    return species_en


def species_to_internal(species: str) -> str:
    """识别到的物种（可能中文或英文）-> 内部英文"""
    return SPECIES_ZH_TO_EN.get(species, species)


def resource_keys_to_display(resources: Dict[str, int], lang: str) -> Dict[str, int]:
    """资源 dict 的 key 按 lang 展示"""
    if lang != "zh":
        return dict(resources)
    return {RESOURCES_EN_TO_ZH.get(k, k): v for k, v in resources.items()}


def resource_key_to_internal(key: str) -> str:
    """资源名（可能中文）-> 内部英文"""
    return RESOURCES_ZH_TO_EN.get(key, key)


def blueprint_name_to_display(name_en: str, lang: str) -> str:
    """蓝图名（内部英文）-> 展示用"""
    if lang == "zh":
        return BUILDINGS_EN_TO_ZH.get(name_en, name_en)
    return name_en


def blueprint_name_to_internal(name: str) -> str:
    """识别到的蓝图名（可能中文）-> 内部英文"""
    return BUILDINGS_ZH_TO_EN.get(name, name)


def translate_analyze_response(response: dict, lang: str) -> dict:
    """
    将分析 API 的响应按 lang 转为展示用（内部始终英文，此处仅改展示字段）。
    lang: "zh" | "en"
    """
    if lang != "zh":
        return response
    out = dict(response)
    gs = out.get("game_state") or {}
    out["game_state"] = {
        **gs,
        "available_blueprints": [blueprint_name_to_display(b, "zh") for b in gs.get("available_blueprints", [])],
        "resources": resource_keys_to_display(gs.get("resources") or {}, "zh"),
        "species": species_to_display(gs.get("species", ""), "zh"),
    }
    recs = out.get("recommendations") or []
    out["recommendations"] = []
    for rec in recs:
        details = rec.get("details") or {}
        out["recommendations"].append({
            **rec,
            "blueprint_name": blueprint_name_to_display(rec.get("blueprint_name", ""), "zh"),
            "details": {
                **details,
                "name": blueprint_name_to_display(details.get("name", ""), "zh"),
                "name_en": details.get("name_en", ""),
                "inputs": {RESOURCES_EN_TO_ZH.get(k, k): v for k, v in (details.get("inputs") or {}).items()},
                "outputs": {RESOURCES_EN_TO_ZH.get(k, k): v for k, v in (details.get("outputs") or {}).items()},
            },
        })
    return out
