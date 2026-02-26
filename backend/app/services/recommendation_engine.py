"""
Recommendation engine for blueprint scoring and ranking
"""
from typing import List, Dict, Tuple, Optional
from app.models import Blueprint, GameState, Recommendation
from app.i18n import RESOURCES_EN_TO_ZH
from app.strategies import (
    StrategyType, EventType, 
    get_strategy_config, get_event_config
)


class RecommendationEngine:
    """Engine for generating blueprint recommendations based on game state"""
    
    def __init__(self, blueprints_data: Dict[str, Blueprint]):
        """
        Initialize recommendation engine
        
        Args:
            blueprints_data: Dictionary mapping blueprint names to Blueprint objects
        """
        self.blueprints_data = blueprints_data
    
    def generate_recommendations(
        self,
        game_state: GameState,
        available_blueprints: List[str],
        top_k: int = 5,
        response_lang: str = "en",
        strategy: Optional[StrategyType] = None,
        event: Optional[EventType] = None
    ) -> List[Recommendation]:
        """
        Generate blueprint recommendations based on game state, strategy and events
        
        Args:
            game_state: Current game state
            available_blueprints: List of available blueprint names
            top_k: Number of top recommendations to return
            response_lang: Language for response ('en' or 'zh')
            strategy: Optional strategy type for scoring adjustment
            event: Optional event type for urgent recommendations
        
        Returns:
            List of Recommendation objects, sorted by priority
            Buildable blueprints are marked and prioritized
        """
        # Get strategy and event configs
        strategy_config = get_strategy_config(strategy) if strategy else get_strategy_config(StrategyType.BALANCED)
        event_config = get_event_config(event) if event else get_event_config(EventType.NONE)
        
        scored_blueprints = []
        
        # Calculate score for each available blueprint
        for blueprint_name in available_blueprints:
            blueprint = self.blueprints_data.get(blueprint_name)
            
            if blueprint is None:
                continue
            
            # Check if blueprint can be built
            buildable = game_state.has_resources_for(blueprint)
            missing_resources = game_state.get_missing_resources(blueprint)
            
            # Calculate base score
            score, reasoning = self._calculate_score(
                blueprint, game_state, response_lang, buildable, missing_resources,
                strategy_config, event_config
            )
            
            scored_blueprints.append({
                'blueprint': blueprint,
                'score': score,
                'reasoning': reasoning,
                'buildable': buildable,
                'missing_resources': missing_resources
            })
        
        # Sort by: buildable first, then by score descending
        scored_blueprints.sort(key=lambda x: (-int(x['buildable']), -x['score']))
        
        # Take top k
        top_blueprints = scored_blueprints[:top_k]
        
        # Create Recommendation objects
        recommendations = []
        for rank, item in enumerate(top_blueprints, start=1):
            recommendation = Recommendation(
                blueprint_name=item['blueprint'].name,
                score=item['score'],
                rank=rank,
                reasoning=item['reasoning'],
                details=item['blueprint'],
                buildable=item['buildable'],
                missing_resources=item['missing_resources']
            )
            recommendations.append(recommendation)
        
        return recommendations
    
    def _calculate_score(
        self,
        blueprint: Blueprint,
        game_state: GameState,
        response_lang: str = "en",
        buildable: bool = True,
        missing_resources: Dict[str, Dict[str, int]] = None,
        strategy_config=None,
        event_config=None
    ) -> Tuple[float, str]:
        """
        Calculate score for a single blueprint with strategy and event adjustments
        
        Args:
            blueprint: Blueprint to score
            game_state: Current game state
            response_lang: Language for reasoning text
            buildable: Whether blueprint can be built with current resources
            missing_resources: Dict of missing resources if not buildable
            strategy_config: Strategy configuration for scoring adjustment
            event_config: Event configuration for urgent recommendations
        
        Returns:
            Tuple of (total_score, reasoning_text)
        """
        scores = {}
        
        # Calculate base value score with strategy/event weights
        base_value = self._calculate_base_value_score_weighted(
            blueprint, strategy_config, event_config
        )
        scores['base_value'] = base_value
        
        # Calculate synergy score
        synergy = self._calculate_synergy_score(blueprint, game_state.species)
        scores['synergy'] = synergy
        
        # Calculate resource score
        resource = self._calculate_resource_score(blueprint, game_state.resources)
        scores['resource'] = resource
        
        # Calculate complexity penalty (with strategy preference)
        complexity_penalty = self._calculate_complexity_penalty_weighted(
            blueprint, strategy_config
        )
        scores['complexity_penalty'] = complexity_penalty
        
        # Add buildable bonus
        scores['buildable_bonus'] = 5.0 if buildable else 0.0
        
        # Add strategy bonus
        strategy_bonus = self._calculate_strategy_bonus(blueprint, strategy_config)
        scores['strategy_bonus'] = strategy_bonus
        
        # Add event bonus (urgent situations)
        event_bonus = self._calculate_event_bonus(blueprint, event_config)
        scores['event_bonus'] = event_bonus
        
        # Calculate total score
        total_score = (base_value + synergy + resource - complexity_penalty + 
                      scores['buildable_bonus'] + strategy_bonus + event_bonus)
        
        reasoning = self._generate_reasoning_v2(
            blueprint, scores, response_lang, buildable, missing_resources or {},
            strategy_config, event_config
        )
        return round(total_score, 1), reasoning
    
    def _calculate_base_value_score(self, blueprint: Blueprint) -> float:
        """
        Calculate base value score: food×10 + fuel×8 + resolve×12
        
        Args:
            blueprint: Blueprint to score
        
        Returns:
            Base value score
        """
        food = blueprint.values.get('food', 0)
        fuel = blueprint.values.get('fuel', 0)
        resolve = blueprint.values.get('resolve', 0)
        
        return food * 10 + fuel * 8 + resolve * 12
    
    def _calculate_synergy_score(
        self,
        blueprint: Blueprint,
        species: str
    ) -> float:
        """
        Calculate species synergy score: +5 if species matches preferences
        
        Args:
            blueprint: Blueprint to score
            species: Current species
        
        Returns:
            Synergy score (0 or 5)
        """
        species_preferences = blueprint.synergy.get('species_preferences', [])
        
        if species in species_preferences:
            return 5.0
        
        return 0.0
    
    def _calculate_resource_score(
        self,
        blueprint: Blueprint,
        resources: Dict[str, int]
    ) -> float:
        """
        Calculate resource availability score: +3 for each abundant resource
        
        Args:
            blueprint: Blueprint to score
            resources: Current resource inventory
        
        Returns:
            Resource score
        """
        score = 0.0
        
        for resource_name, required_amount in blueprint.inputs.items():
            available_amount = resources.get(resource_name, 0)
            
            # Consider resource abundant if we have >= 10 units
            if available_amount >= 10:
                score += 3.0
        
        return score
    
    def _calculate_complexity_penalty(self, blueprint: Blueprint) -> float:
        """
        Calculate complexity penalty: complexity × 4
        
        Args:
            blueprint: Blueprint to score
        
        Returns:
            Complexity penalty
        """
        return blueprint.complexity * 4.0
    
    def _generate_reasoning(
        self,
        blueprint: Blueprint,
        scores: Dict[str, float],
        response_lang: str = "en",
        buildable: bool = True,
        missing_resources: Dict[str, Dict[str, int]] = None
    ) -> str:
        """Generate reasoning text in English or Chinese."""
        if response_lang == "zh":
            return self._reasoning_zh(blueprint, scores, buildable, missing_resources or {})
        return self._reasoning_en(blueprint, scores, buildable, missing_resources or {})

    def _reasoning_en(self, blueprint: Blueprint, scores: Dict[str, float], buildable: bool, missing_resources: Dict[str, Dict[str, int]]) -> str:
        parts = []
        
        # Buildable status
        if buildable:
            parts.append("✅ Can be built now")
            if scores.get('buildable_bonus', 0) > 0:
                parts.append(f"Buildable bonus: +{int(scores['buildable_bonus'])} pts")
        else:
            parts.append("❌ Cannot build - insufficient resources")
            if missing_resources:
                missing_details = []
                for res, details in missing_resources.items():
                    missing_details.append(f"{res}: need {details['required']}, have {details['available']}")
                parts.append(f"Missing: {'; '.join(missing_details)}")
        
        if scores['base_value'] > 0:
            food = blueprint.values.get('food', 0)
            fuel = blueprint.values.get('fuel', 0)
            resolve = blueprint.values.get('resolve', 0)
            value_details = []
            if food > 0:
                value_details.append(f"food {food}×10")
            if fuel > 0:
                value_details.append(f"fuel {fuel}×8")
            if resolve > 0:
                value_details.append(f"resolve {resolve}×12")
            if value_details:
                parts.append(f"Base value: {int(scores['base_value'])} pts ({' + '.join(value_details)})")
        if scores['synergy'] > 0:
            parts.append(f"Species synergy: +{int(scores['synergy'])} pts")
        if scores['resource'] > 0:
            abundant = list(blueprint.inputs.keys())
            if abundant:
                parts.append(f"Resource bonus: +{int(scores['resource'])} pts ({', '.join(abundant)})")
        if scores['complexity_penalty'] > 0:
            parts.append(f"Complexity penalty: -{int(scores['complexity_penalty'])} pts (complexity {blueprint.complexity}×4)")
        if scores.get('strategy_bonus', 0) > 0:
            parts.append(f"Strategy bonus: +{int(scores['strategy_bonus'])} pts")
        if scores.get('event_bonus', 0) > 0:
            parts.append(f"🚨 Event bonus: +{int(scores['event_bonus'])} pts (URGENT)")
        total = (scores['base_value'] + scores['synergy'] + scores['resource'] - 
                scores['complexity_penalty'] + scores.get('buildable_bonus', 0) +
                scores.get('strategy_bonus', 0) + scores.get('event_bonus', 0))
        parts.append(f"Total: {round(total, 1)} pts")
        return "\n".join(parts)

    def _reasoning_zh(self, blueprint: Blueprint, scores: Dict[str, float], buildable: bool, missing_resources: Dict[str, Dict[str, int]]) -> str:
        parts = []
        
        # 可建造状态
        if buildable:
            parts.append("✅ 可立即建造")
            if scores.get('buildable_bonus', 0) > 0:
                parts.append(f"可建造奖励: +{int(scores['buildable_bonus'])}分")
        else:
            parts.append("❌ 资源不足，无法建造")
            if missing_resources:
                missing_details = []
                for res, details in missing_resources.items():
                    missing_details.append(f"{res}: 需{details['required']}/有{details['available']}")
                parts.append(f"缺口: {'; '.join(missing_details)}")
        
        if scores['base_value'] > 0:
            food = blueprint.values.get('food', 0)
            fuel = blueprint.values.get('fuel', 0)
            resolve = blueprint.values.get('resolve', 0)
            value_details = []
            if food > 0:
                value_details.append(f"食物{food}×10")
            if fuel > 0:
                value_details.append(f"燃料{fuel}×8")
            if resolve > 0:
                value_details.append(f"决心{resolve}×12")
            if value_details:
                parts.append(f"基础价值分: {int(scores['base_value'])}分 ({' + '.join(value_details)})")
        if scores['synergy'] > 0:
            parts.append(f"种族协同: +{int(scores['synergy'])}分")
        if scores['resource'] > 0:
            abundant = list(blueprint.inputs.keys())
            if abundant:
                parts.append(f"资源充足: +{int(scores['resource'])}分 ({', '.join(abundant)})")
        if scores['complexity_penalty'] > 0:
            parts.append(f"复杂度惩罚: -{int(scores['complexity_penalty'])}分 (复杂度{blueprint.complexity}×4)")
        if scores.get('strategy_bonus', 0) > 0:
            parts.append(f"策略加成: +{int(scores['strategy_bonus'])}分")
        if scores.get('event_bonus', 0) > 0:
            parts.append(f"事件加成: +{int(scores['event_bonus'])}分 ⚠️")
        total = (scores['base_value'] + scores['synergy'] + scores['resource'] - 
                scores['complexity_penalty'] + scores.get('buildable_bonus', 0) +
                scores.get('strategy_bonus', 0) + scores.get('event_bonus', 0))
        parts.append(f"总分: {round(total, 1)}分")
        return "\n".join(parts)
    
    # ============== Strategy & Event Enhanced Methods ==============
    
    def _calculate_base_value_score_weighted(
        self,
        blueprint: Blueprint,
        strategy_config,
        event_config
    ) -> float:
        """Calculate base value score with strategy and event weights"""
        food = blueprint.values.get('food', 0)
        fuel = blueprint.values.get('fuel', 0)
        resolve = blueprint.values.get('resolve', 0)
        
        # Get weights from strategy and event
        s_weights = strategy_config.value_weights if strategy_config else {'food': 1.0, 'fuel': 1.0, 'resolve': 1.0}
        e_weights = event_config.value_weights if event_config else {}
        
        # Combine weights (event weights override strategy)
        w_food = e_weights.get('food', s_weights.get('food', 1.0))
        w_fuel = e_weights.get('fuel', s_weights.get('fuel', 1.0))
        w_resolve = e_weights.get('resolve', s_weights.get('resolve', 1.0))
        
        return food * 10 * w_food + fuel * 8 * w_fuel + resolve * 12 * w_resolve
    
    def _calculate_complexity_penalty_weighted(
        self,
        blueprint: Blueprint,
        strategy_config
    ) -> float:
        """Calculate complexity penalty with strategy preference"""
        base_penalty = blueprint.complexity * 4.0
        
        if not strategy_config:
            return base_penalty
        
        pref = strategy_config.complexity_preference
        complexity = blueprint.complexity
        
        # Adjust penalty based on strategy preference
        if pref == 'low' and complexity <= 2:
            return base_penalty * 0.5  # Favor simple buildings
        elif pref == 'low' and complexity >= 4:
            return base_penalty * 1.5  # Discourage complex
        elif pref == 'high' and complexity >= 4:
            return base_penalty * 0.5  # Favor complex buildings
        elif pref == 'high' and complexity <= 2:
            return base_penalty * 1.2  # Slightly discourage simple
        
        return base_penalty
    
    def _calculate_strategy_bonus(
        self,
        blueprint: Blueprint,
        strategy_config
    ) -> float:
        """Calculate strategy-specific bonus"""
        if not strategy_config:
            return 0.0
        
        bonus = 0.0
        
        # Check if blueprint is in strategy's recommended list
        if blueprint.name in strategy_config.blueprint_boost:
            bonus += strategy_config.score_bonus
        
        return bonus
    
    def _calculate_event_bonus(
        self,
        blueprint: Blueprint,
        event_config
    ) -> float:
        """Calculate event-specific bonus for urgent situations"""
        if not event_config:
            return 0.0
        
        bonus = 0.0
        
        # Check if blueprint produces required outputs
        for output in event_config.required_outputs:
            if output in blueprint.outputs:
                bonus += event_config.score_bonus
                break  # Only count once
        
        # Check if blueprint is in event's recommended list
        if blueprint.name in event_config.blueprint_boost:
            bonus += event_config.score_bonus * 0.5
        
        return bonus
    
    def _generate_reasoning_v2(
        self,
        blueprint: Blueprint,
        scores: Dict[str, float],
        response_lang: str,
        buildable: bool,
        missing_resources: Dict[str, Dict[str, int]],
        strategy_config,
        event_config
    ) -> str:
        """Generate enhanced reasoning with strategy and event info"""
        if response_lang == "zh":
            return self._reasoning_zh_v2(
                blueprint, scores, buildable, missing_resources,
                strategy_config, event_config
            )
        return self._reasoning_en_v2(
            blueprint, scores, buildable, missing_resources,
            strategy_config, event_config
        )
    
    def _reasoning_en_v2(
        self,
        blueprint: Blueprint,
        scores: Dict[str, float],
        buildable: bool,
        missing_resources: Dict[str, Dict[str, int]],
        strategy_config,
        event_config
    ) -> str:
        """Generate English reasoning with strategy and event info"""
        parts = []
        
        # Strategy and event context
        if strategy_config and strategy_config.type != 'balanced':
            parts.append(f"📊 Strategy: {strategy_config.name_en}")
        if event_config and event_config.urgent:
            parts.append(f"🚨 URGENT: {event_config.name_en}")
        
        # Buildable status
        if buildable:
            parts.append("✅ Can be built now")
            if scores.get('buildable_bonus', 0) > 0:
                parts.append(f"Buildable bonus: +{int(scores['buildable_bonus'])} pts")
        else:
            parts.append("❌ Cannot build - insufficient resources")
            if missing_resources:
                missing_details = []
                for res, details in missing_resources.items():
                    missing_details.append(f"{res}: need {details['required']}, have {details['available']}")
                parts.append(f"Missing: {'; '.join(missing_details)}")
        
        # Base value with weights indication
        if scores['base_value'] > 0:
            food = blueprint.values.get('food', 0)
            fuel = blueprint.values.get('fuel', 0)
            resolve = blueprint.values.get('resolve', 0)
            value_details = []
            if food > 0:
                value_details.append(f"food {food}×10")
            if fuel > 0:
                value_details.append(f"fuel {fuel}×8")
            if resolve > 0:
                value_details.append(f"resolve {resolve}×12")
            if value_details:
                parts.append(f"Base value: {int(scores['base_value'])} pts ({' + '.join(value_details)})")
        
        if scores['synergy'] > 0:
            parts.append(f"Species synergy: +{int(scores['synergy'])} pts")
        if scores['resource'] > 0:
            abundant = list(blueprint.inputs.keys())
            if abundant:
                parts.append(f"Resource bonus: +{int(scores['resource'])} pts ({', '.join(abundant)})")
        if scores['complexity_penalty'] > 0:
            parts.append(f"Complexity penalty: -{int(scores['complexity_penalty'])} pts (complexity {blueprint.complexity}×4)")
        if scores.get('strategy_bonus', 0) > 0:
            parts.append(f"Strategy bonus: +{int(scores['strategy_bonus'])} pts")
        if scores.get('event_bonus', 0) > 0:
            parts.append(f"🚨 Event bonus: +{int(scores['event_bonus'])} pts (URGENT)")
        
        total = (scores['base_value'] + scores['synergy'] + scores['resource'] - 
                scores['complexity_penalty'] + scores.get('buildable_bonus', 0) +
                scores.get('strategy_bonus', 0) + scores.get('event_bonus', 0))
        parts.append(f"Total: {round(total, 1)} pts")
        return "\n".join(parts)
    
    def _reasoning_zh_v2(
        self,
        blueprint: Blueprint,
        scores: Dict[str, float],
        buildable: bool,
        missing_resources: Dict[str, Dict[str, int]],
        strategy_config,
        event_config
    ) -> str:
        """Generate Chinese reasoning with strategy and event info"""
        parts = []
        
        # 策略和事件上下文
        if strategy_config:
            parts.append(f"📊 运营方向: {strategy_config.name}")
        if event_config and event_config.urgent:
            parts.append(f"🚨 紧急事件: {event_config.name}")
        
        # 可建造状态
        if buildable:
            parts.append("✅ 可立即建造")
            if scores.get('buildable_bonus', 0) > 0:
                parts.append(f"可建造奖励: +{int(scores['buildable_bonus'])}分")
        else:
            parts.append("❌ 资源不足，无法建造")
            if missing_resources:
                missing_details = []
                for res, details in missing_resources.items():
                    missing_details.append(f"{res}: 需{details['required']}/有{details['available']}")
                parts.append(f"缺口: {'; '.join(missing_details)}")
        
        # 基础价值
        if scores['base_value'] > 0:
            food = blueprint.values.get('food', 0)
            fuel = blueprint.values.get('fuel', 0)
            resolve = blueprint.values.get('resolve', 0)
            value_details = []
            if food > 0:
                value_details.append(f"食物{food}×10")
            if fuel > 0:
                value_details.append(f"燃料{fuel}×8")
            if resolve > 0:
                value_details.append(f"决心{resolve}×12")
            if value_details:
                parts.append(f"基础价值分: {int(scores['base_value'])}分 ({' + '.join(value_details)})")
        
        if scores['synergy'] > 0:
            parts.append(f"种族协同: +{int(scores['synergy'])}分")
        if scores['resource'] > 0:
            abundant = list(blueprint.inputs.keys())
            if abundant:
                parts.append(f"资源充足: +{int(scores['resource'])}分 ({', '.join(abundant)})")
        if scores['complexity_penalty'] > 0:
            parts.append(f"复杂度惩罚: -{int(scores['complexity_penalty'])}分 (复杂度{blueprint.complexity}×4)")
        if scores.get('strategy_bonus', 0) > 0:
            parts.append(f"策略加成: +{int(scores['strategy_bonus'])}分")
        if scores.get('event_bonus', 0) > 0:
            parts.append(f"🚨 事件加成: +{int(scores['event_bonus'])}分 (紧急)")
        
        total = (scores['base_value'] + scores['synergy'] + scores['resource'] - 
                scores['complexity_penalty'] + scores.get('buildable_bonus', 0) +
                scores.get('strategy_bonus', 0) + scores.get('event_bonus', 0))
        parts.append(f"总分: {round(total, 1)}分")
        return "\n".join(parts)
