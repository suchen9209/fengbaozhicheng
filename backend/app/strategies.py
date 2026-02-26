"""
Game strategy and event definitions for recommendation engine
"""
from enum import Enum
from typing import Dict, List, Optional
from dataclasses import dataclass


class StrategyType(str, Enum):
    """运营方向/策略类型"""
    BALANCED = "balanced"           # 平衡发展
    FOOD_FIRST = "food_first"       # 食物优先 - 解决食物短缺、支持人口增长
    FUEL_FIRST = "fuel_first"       # 燃料优先 - 应对风暴季、冬季
    RESOLVE_FIRST = "resolve_first" # 决心优先 - 提升居民满意度
    PRODUCTION_CHAIN = "production_chain"  # 产业链完善 - 上下游配套
    DEFENSE = "defense"             # 防御强化 - 应对威胁
    GROWTH = "growth"               # 快速扩张 - 多造建筑


class EventType(str, Enum):
    """游戏事件类型"""
    NONE = "none"
    FOOD_SHORTAGE = "food_shortage"       # 食物短缺
    FUEL_SHORTAGE = "fuel_shortage"       # 燃料短缺
    LOW_RESOLVE = "low_resolve"           # 决心低落
    DISEASE = "disease"                   # 疾病爆发
    ENEMY_THREAT = "enemy_threat"         # 敌人威胁
    STORM_SEASON = "storm_season"         # 风暴季来临
    POPULATION_BOOM = "population_boom"   # 人口激增
    RESOURCE_CRISIS = "resource_crisis"   # 资源危机（综合）


@dataclass
class StrategyConfig:
    """策略配置"""
    name: str                           # 显示名称
    name_en: str                        # 英文名
    description: str                    # 描述
    value_weights: Dict[str, float]     # 价值权重调整 {food: 1.5, fuel: 1.0, ...}
    input_weights: Dict[str, float]     # 输入资源权重（优先使用充足资源）
    complexity_preference: str          # 复杂度偏好 "low"/"medium"/"high"/"any"
    blueprint_boost: List[str]          # 特定蓝图加成
    score_bonus: float                  # 总分加成


@dataclass
class EventConfig:
    """事件配置"""
    name: str                           # 显示名称
    name_en: str                        # 英文名
    description: str                    # 描述
    urgent: bool                        # 是否紧急
    value_weights: Dict[str, float]     # 价值权重调整
    required_outputs: List[str]         # 需要的产出类型
    blueprint_boost: List[str]          # 推荐蓝图
    score_bonus: float                  # 紧急加分


# 策略定义
STRATEGIES: Dict[StrategyType, StrategyConfig] = {
    StrategyType.BALANCED: StrategyConfig(
        name="平衡发展",
        name_en="Balanced",
        description="均衡发展各类资源，不追求单一方向",
        value_weights={"food": 1.0, "fuel": 1.0, "resolve": 1.0},
        input_weights={},
        complexity_preference="any",
        blueprint_boost=[],
        score_bonus=0
    ),
    
    StrategyType.FOOD_FIRST: StrategyConfig(
        name="食物优先",
        name_en="Food First",
        description="优先保证食物供应，适合食物短缺或人口增长期",
        value_weights={"food": 2.0, "fuel": 0.8, "resolve": 0.8},
        input_weights={"食物": 0.5},  # 优先不消耗食物的
        complexity_preference="low",
        blueprint_boost=["农场", "面包房", "渔场", "狩猎小屋", "磨坊"],
        score_bonus=5
    ),
    
    StrategyType.FUEL_FIRST: StrategyConfig(
        name="燃料优先",
        name_en="Fuel First",
        description="优先保证燃料供应，适合风暴季或冬季准备",
        value_weights={"food": 0.8, "fuel": 2.0, "resolve": 0.8},
        input_weights={},
        complexity_preference="any",
        blueprint_boost=["伐木场", "窑", "矿场", "锻造厂"],
        score_bonus=5
    ),
    
    StrategyType.RESOLVE_FIRST: StrategyConfig(
        name="决心优先",
        name_en="Resolve First",
        description="优先提升居民决心/满意度，适合低士气时",
        value_weights={"food": 0.8, "fuel": 0.8, "resolve": 2.0},
        input_weights={},
        complexity_preference="medium",
        blueprint_boost=["酒馆", "神殿", "图书馆", "药剂铺", "炼金工坊"],
        score_bonus=5
    ),
    
    StrategyType.PRODUCTION_CHAIN: StrategyConfig(
        name="产业链完善",
        name_en="Production Chain",
        description="完善上下游产业链，追求资源转化效率",
        value_weights={"food": 1.0, "fuel": 1.0, "resolve": 1.0},
        input_weights={},
        complexity_preference="high",
        blueprint_boost=["磨坊", "面包房", "铁匠铺", "工坊", "锻造厂", "炼金工坊"],
        score_bonus=3
    ),
    
    StrategyType.DEFENSE: StrategyConfig(
        name="防御强化",
        name_en="Defense Focus",
        description="强化防御能力，应对敌人威胁",
        value_weights={"food": 0.8, "fuel": 1.0, "resolve": 1.2},
        input_weights={},
        complexity_preference="any",
        blueprint_boost=["兵营", "训练场", "铁匠铺", "锻造厂"],
        score_bonus=5
    ),
    
    StrategyType.GROWTH: StrategyConfig(
        name="快速扩张",
        name_en="Rapid Growth",
        description="快速建造简单建筑，扩张基地规模",
        value_weights={"food": 1.2, "fuel": 1.0, "resolve": 0.8},
        input_weights={},
        complexity_preference="low",
        blueprint_boost=["伐木场", "农场", "小农场", "采集者营地"],
        score_bonus=3
    ),
}


# 事件定义
EVENTS: Dict[EventType, EventConfig] = {
    EventType.NONE: EventConfig(
        name="无特殊事件",
        name_en="None",
        description="当前没有特殊事件",
        urgent=False,
        value_weights={},
        required_outputs=[],
        blueprint_boost=[],
        score_bonus=0
    ),
    
    EventType.FOOD_SHORTAGE: EventConfig(
        name="食物短缺",
        name_en="Food Shortage",
        description="食物储备不足，需要紧急增加食物产出",
        urgent=True,
        value_weights={"food": 3.0, "fuel": 0.5, "resolve": 0.8},
        required_outputs=["食物", "肉", "鱼", "面包"],
        blueprint_boost=["农场", "面包房", "渔场", "狩猎小屋"],
        score_bonus=15
    ),
    
    EventType.FUEL_SHORTAGE: EventConfig(
        name="燃料短缺",
        name_en="Fuel Shortage",
        description="燃料储备不足，可能影响过冬",
        urgent=True,
        value_weights={"food": 0.8, "fuel": 3.0, "resolve": 0.5},
        required_outputs=["木材", "煤炭"],
        blueprint_boost=["伐木场", "窑"],
        score_bonus=15
    ),
    
    EventType.LOW_RESOLVE: EventConfig(
        name="决心低落",
        name_en="Low Resolve",
        description="居民决心低落，可能引发离开或暴乱",
        urgent=True,
        value_weights={"food": 0.8, "fuel": 0.5, "resolve": 3.0},
        required_outputs=[],
        blueprint_boost=["酒馆", "神殿", "图书馆"],
        score_bonus=15
    ),
    
    EventType.DISEASE: EventConfig(
        name="疾病爆发",
        name_en="Disease Outbreak",
        description="疾病蔓延，需要医疗设施",
        urgent=True,
        value_weights={"food": 1.0, "fuel": 0.5, "resolve": 2.0},
        required_outputs=["药剂"],
        blueprint_boost=["药剂铺", "神殿"],
        score_bonus=20
    ),
    
    EventType.ENEMY_THREAT: EventConfig(
        name="敌人威胁",
        name_en="Enemy Threat",
        description="检测到敌人威胁，需要防御准备",
        urgent=True,
        value_weights={"food": 0.5, "fuel": 0.8, "resolve": 1.5},
        required_outputs=["武器"],
        blueprint_boost=["兵营", "训练场", "铁匠铺"],
        score_bonus=20
    ),
    
    EventType.STORM_SEASON: EventConfig(
        name="风暴季来临",
        name_en="Storm Season",
        description="风暴季即将开始，需要储备燃料和食物",
        urgent=False,
        value_weights={"food": 1.5, "fuel": 2.0, "resolve": 1.0},
        required_outputs=[],
        blueprint_boost=["伐木场", "窑", "农场"],
        score_bonus=8
    ),
    
    EventType.POPULATION_BOOM: EventConfig(
        name="人口激增",
        name_en="Population Boom",
        description="人口快速增长，食物和住房压力增大",
        urgent=False,
        value_weights={"food": 2.0, "fuel": 1.0, "resolve": 0.8},
        required_outputs=["食物"],
        blueprint_boost=["农场", "面包房", "酒馆"],
        score_bonus=10
    ),
    
    EventType.RESOURCE_CRISIS: EventConfig(
        name="资源危机",
        name_en="Resource Crisis",
        description="多种资源短缺，需要综合应对",
        urgent=True,
        value_weights={"food": 1.5, "fuel": 1.5, "resolve": 1.0},
        required_outputs=[],
        blueprint_boost=["伐木场", "农场", "矿场"],
        score_bonus=12
    ),
}


def get_strategy_config(strategy: StrategyType) -> StrategyConfig:
    """Get strategy configuration"""
    return STRATEGIES.get(strategy, STRATEGIES[StrategyType.BALANCED])


def get_event_config(event: EventType) -> EventConfig:
    """Get event configuration"""
    return EVENTS.get(event, EVENTS[EventType.NONE])


def get_all_strategies() -> List[Dict]:
    """Get all strategies as list of dicts for API"""
    return [
        {
            "type": s_type.value,
            "name": config.name,
            "name_en": config.name_en,
            "description": config.description
        }
        for s_type, config in STRATEGIES.items()
    ]


def get_all_events() -> List[Dict]:
    """Get all events as list of dicts for API"""
    return [
        {
            "type": e_type.value,
            "name": config.name,
            "name_en": config.name_en,
            "description": config.description,
            "urgent": config.urgent
        }
        for e_type, config in EVENTS.items()
    ]
