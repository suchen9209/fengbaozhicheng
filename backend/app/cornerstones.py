"""
Cornerstone (基石) definitions and effects for recommendation engine
"""
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum


class CornerstoneEffectType(str, Enum):
    """基石效果类型"""
    PRODUCTION_SPEED = "production_speed"      # 生产速度加成
    YIELD_BONUS = "yield_bonus"                # 产量加成
    RESOURCE_BONUS = "resource_bonus"          # 资源产出加成
    BUILDING_BOOST = "building_boost"          # 特定建筑加成
    GLOBAL_BOOST = "global_boost"              # 全局加成
    TRADE_BOOST = "trade_boost"                # 交易加成
    RESOLVE_BOOST = "resolve_boost"            # 决心加成


@dataclass
class CornerstoneEffect:
    """基石效果"""
    effect_type: CornerstoneEffectType
    target_buildings: List[str]                # 目标建筑列表（英文slug）
    target_resources: List[str]                # 目标资源列表
    multiplier: float                          # 加成倍数 (1.25 = +25%)
    description: str                           # 效果描述


@dataclass
class Cornerstone:
    """基石定义"""
    name: str                                  # 英文名
    name_zh: str                               # 中文名（可补充）
    effect: str                                # 原始效果描述
    rarity: str                                # 稀有度
    effects: List[CornerstoneEffect]           # 解析后的效果列表


# 解析后的基石数据（关键基石）
# 根据效果分类，影响推荐优先级
CORNERSTONES: Dict[str, Cornerstone] = {
    # 农场/食物相关
    "back_to_nature": Cornerstone(
        name="Back to Nature",
        name_zh="回归自然",
        effect="Increases yields by 100% in all Buildings that use Fertile Soil (Farms). You will lose all stored food upon choosing this cornerstone.",
        rarity="Legendary",
        effects=[
            CornerstoneEffect(
                effect_type=CornerstoneEffectType.BUILDING_BOOST,
                target_buildings=["farm", "small_farm", "plantation", "greenhouse", "herb_garden"],
                target_resources=[],
                multiplier=2.0,  # +100%
                description="农场类建筑产量翻倍"
            )
        ]
    ),
    
    "biscuit_diet": Cornerstone(
        name="Biscuit Diet",
        name_zh="饼干饮食",
        effect="Farmers have a +75% chance of producing double yields when under the effect of Biscuits.",
        rarity="Epic",
        effects=[
            CornerstoneEffect(
                effect_type=CornerstoneEffectType.BUILDING_BOOST,
                target_buildings=["farm", "small_farm"],
                target_resources=[],
                multiplier=1.75,  # 近似效果
                description="农场双倍产出概率+75%"
            )
        ]
    ),
    
    "bread_peels": Cornerstone(
        name="Bread Peels",
        name_zh="面包铲",
        effect="Bakery production is 50% quicker.",
        rarity="Epic",
        effects=[
            CornerstoneEffect(
                effect_type=CornerstoneEffectType.BUILDING_BOOST,
                target_buildings=["bakery"],
                target_resources=[],
                multiplier=1.5,
                description="面包房生产速度+50%"
            )
        ]
    ),
    
    "cooking_steam": Cornerstone(
        name="Cooking Steam",
        name_zh="烹饪蒸汽",
        effect="Food production speed is increased by +10% for every 50 units of drizzle water stored.",
        rarity="Legendary",
        effects=[
            CornerstoneEffect(
                effect_type=CornerstoneEffectType.GLOBAL_BOOST,
                target_buildings=["bakery", "cookhouse", "field_kitchen", "grill", "smokehouse", "butcher"],
                target_resources=[],
                multiplier=1.3,  # 假设平均效果
                description="食物生产建筑速度提升"
            )
        ]
    ),
    
    # 燃料相关
    "advanced_fuel": Cornerstone(
        name="Advanced Fuel",
        name_zh="高级燃料",
        effect="All Fuel Recipes are 25% faster.",
        rarity="Epic",
        effects=[
            CornerstoneEffect(
                effect_type=CornerstoneEffectType.GLOBAL_BOOST,
                target_buildings=["kiln", "smokehouse", "brick_oven", "grill"],
                target_resources=[],
                multiplier=1.25,
                description="燃料生产速度+25%"
            )
        ]
    ),
    
    # 采集类建筑
    "hunter_gatherers": Cornerstone(
        name="Hunter–Gatherers",
        name_zh="狩猎采集者",
        effect="All Camp production is increased by 50%, but all Buildings that use Fertile Soil have their yields decreased by 50%.",
        rarity="Legendary",
        effects=[
            CornerstoneEffect(
                effect_type=CornerstoneEffectType.BUILDING_BOOST,
                target_buildings=["woodcutters_camp", "harvesters_camp", "foragers_camp", "trappers_camp", "herbalists_camp", "stonecutters_camp"],
                target_resources=[],
                multiplier=1.5,
                description="采集营地产量+50%"
            ),
            CornerstoneEffect(
                effect_type=CornerstoneEffectType.BUILDING_BOOST,
                target_buildings=["farm", "small_farm", "plantation"],
                target_resources=[],
                multiplier=0.5,  # 减益
                description="农场产量-50%"
            )
        ]
    ),
    
    # 金属/工业
    "copper_extractor": Cornerstone(
        name="Copper Extractor",
        name_zh="铜矿提取器",
        effect="Gain 1 Copper Ore for every 5 Wood produced. All Crystalized Dew production is reduced by 1",
        rarity="Legendary",
        effects=[
            CornerstoneEffect(
                effect_type=CornerstoneEffectType.RESOURCE_BONUS,
                target_buildings=["woodcutters_camp"],
                target_resources=["copper_ore"],
                multiplier=1.2,
                description="伐木附带铜矿产出"
            )
        ]
    ),
    
    # 贸易
    "deserted_caravans": Cornerstone(
        name="Deserted Caravans",
        name_zh="废弃商队",
        effect="Global production is 50% faster, but Trading is unavailable.",
        rarity="Legendary",
        effects=[
            CornerstoneEffect(
                effect_type=CornerstoneEffectType.GLOBAL_BOOST,
                target_buildings=[],  # 所有
                target_resources=[],
                multiplier=1.5,
                description="全局生产速度+50%"
            )
        ]
    ),
    
    # 决心相关
    "ancient_artifact": Cornerstone(
        name="Ancient Artifact",
        name_zh="远古遗物",
        effect="A strange device left behind by the Great Civilization. When soaked in rainwater, it radiates warm light and brings encouragement to those around it. (+3 to Global Resolve)",
        rarity="Epic",
        effects=[
            CornerstoneEffect(
                effect_type=CornerstoneEffectType.RESOLVE_BOOST,
                target_buildings=[],
                target_resources=[],
                multiplier=1.0,
                description="全局决心+3"
            )
        ]
    ),
    
    # 仓储相关
    "export_specialization": Cornerstone(
        name="Export Specialization",
        name_zh="出口专业化",
        effect="Gain +1 to production yields for all Packs of Goods.",
        rarity="Epic",
        effects=[
            CornerstoneEffect(
                effect_type=CornerstoneEffectType.GLOBAL_BOOST,
                target_buildings=["guild_house", "market"],
                target_resources=[],
                multiplier=1.2,
                description="包装货物产量+1"
            )
        ]
    ),
}


# 建筑名称到 slug 的映射（用于匹配）
BUILDING_NAME_MAP = {
    "农场": "farm",
    "小农场": "small_farm",
    "种植园": "plantation",
    "温室": "greenhouse",
    "草药园": "herb_garden",
    "面包房": "bakery",
    "厨房": "cookhouse",
    "野战厨房": "field_kitchen",
    "烧烤架": "grill",
    "熏制房": "smokehouse",
    "屠宰场": "butcher",
    "窑": "kiln",
    "砖炉": "brick_oven",
    "伐木营地": "woodcutters_camp",
    "收割者营地": "harvesters_camp",
    "采集者营地": "foragers_camp",
    "陷阱师营地": "trappers_camp",
    "草药师营地": "herbalists_camp",
    "石匠营地": "stonecutters_camp",
    "矿场": "mine",
    "采石场": "quarry",
}


def get_cornerstone(cornerstone_id: str) -> Optional[Cornerstone]:
    """Get cornerstone by ID"""
    return CORNERSTONES.get(cornerstone_id)


def get_all_cornerstones() -> List[Dict]:
    """Get all cornerstones for API"""
    return [
        {
            "id": cid,
            "name": c.name,
            "name_zh": c.name_zh,
            "effect": c.effect,
            "rarity": c.rarity,
            "effects": [
                {
                    "type": e.effect_type.value,
                    "target_buildings": e.target_buildings,
                    "target_resources": e.target_resources,
                    "multiplier": e.multiplier,
                    "description": e.description
                }
                for e in c.effects
            ]
        }
        for cid, c in CORNERSTONES.items()
    ]


def calculate_cornerstone_bonus(
    blueprint_name: str,
    blueprint_name_en: str,
    active_cornerstones: List[str]
) -> float:
    """
    Calculate bonus multiplier from active cornerstones for a blueprint
    
    Args:
        blueprint_name: 蓝图中文名
        blueprint_name_en: 蓝图英文名
        active_cornerstones: 激活的基石ID列表
        
    Returns:
        总加成倍数 (1.0 = 无加成，1.5 = +50%)
    """
    total_multiplier = 1.0
    
    # 获取蓝图 slug
    blueprint_slug = blueprint_name_en.lower().replace(" ", "_").replace("'", "")
    
    for cid in active_cornerstones:
        cs = get_cornerstone(cid)
        if not cs:
            continue
            
        for effect in cs.effects:
            # 检查是否影响此建筑
            if blueprint_slug in effect.target_buildings:
                # 累加加成（乘法叠加）
                total_multiplier *= effect.multiplier
            
            # 全局加成
            if effect.effect_type == CornerstoneEffectType.GLOBAL_BOOST and not effect.target_buildings:
                total_multiplier *= effect.multiplier
    
    return round(total_multiplier, 2)


def get_recommended_cornerstones(
    available_blueprints: List[str],
    strategy: str
) -> List[str]:
    """
    Recommend cornerstones based on available blueprints and strategy
    
    Returns:
        推荐的基石ID列表
    """
    recommendations = []
    
    # 如果有农场类建筑，推荐农场相关基石
    farm_buildings = ["农场", "小农场", "种植园"]
    if any(bp in farm_buildings for bp in available_blueprints):
        recommendations.append("back_to_nature")
        recommendations.append("biscuit_diet")
    
    # 如果有面包房
    if "面包房" in available_blueprints:
        recommendations.append("bread_peels")
    
    # 如果有采集营地
    camp_buildings = ["伐木营地", "采集者营地", "陷阱师营地"]
    if any(bp in camp_buildings for bp in available_blueprints):
        recommendations.append("hunter_gatherers")
    
    # 根据策略
    if strategy == "food_first":
        recommendations.extend(["back_to_nature", "biscuit_diet", "cooking_steam"])
    elif strategy == "fuel_first":
        recommendations.append("advanced_fuel")
    elif strategy == "resolve_first":
        recommendations.append("ancient_artifact")
    
    return list(set(recommendations))  # 去重
