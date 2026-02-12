"""
Recommendation engine for blueprint scoring and ranking
"""
from typing import List, Dict, Tuple
from app.models import Blueprint, GameState, Recommendation
from app.i18n import RESOURCES_EN_TO_ZH


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
        response_lang: str = "en"
    ) -> List[Recommendation]:
        """
        Generate blueprint recommendations based on game state
        
        Args:
            game_state: Current game state
            available_blueprints: List of available blueprint names
            top_k: Number of top recommendations to return
        
        Returns:
            List of Recommendation objects, sorted by score descending
        """
        scored_blueprints = []
        
        # Calculate score for each available blueprint
        for blueprint_name in available_blueprints:
            blueprint = self.blueprints_data.get(blueprint_name)
            
            if blueprint is None:
                # Blueprint not found in data, skip
                continue
            
            score, reasoning = self._calculate_score(blueprint, game_state, response_lang)
            
            scored_blueprints.append({
                'blueprint': blueprint,
                'score': score,
                'reasoning': reasoning
            })
        
        # Sort by score descending
        scored_blueprints.sort(key=lambda x: x['score'], reverse=True)
        
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
                details=item['blueprint']
            )
            recommendations.append(recommendation)
        
        return recommendations
    
    def _calculate_score(
        self,
        blueprint: Blueprint,
        game_state: GameState,
        response_lang: str = "en"
    ) -> Tuple[float, str]:
        """
        Calculate score for a single blueprint
        
        Args:
            blueprint: Blueprint to score
            game_state: Current game state
        
        Returns:
            Tuple of (total_score, reasoning_text)
        """
        scores = {}
        
        # Calculate base value score
        base_value = self._calculate_base_value_score(blueprint)
        scores['base_value'] = base_value
        
        # Calculate synergy score
        synergy = self._calculate_synergy_score(blueprint, game_state.species)
        scores['synergy'] = synergy
        
        # Calculate resource score
        resource = self._calculate_resource_score(blueprint, game_state.resources)
        scores['resource'] = resource
        
        # Calculate complexity penalty
        complexity_penalty = self._calculate_complexity_penalty(blueprint)
        scores['complexity_penalty'] = complexity_penalty
        
        # Calculate total score
        total_score = base_value + synergy + resource - complexity_penalty
        
        reasoning = self._generate_reasoning(blueprint, scores, response_lang)
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
        response_lang: str = "en"
    ) -> str:
        """Generate reasoning text in English or Chinese."""
        if response_lang == "zh":
            return self._reasoning_zh(blueprint, scores)
        return self._reasoning_en(blueprint, scores)

    def _reasoning_en(self, blueprint: Blueprint, scores: Dict[str, float]) -> str:
        parts = []
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
        total = scores['base_value'] + scores['synergy'] + scores['resource'] - scores['complexity_penalty']
        parts.append(f"Total: {round(total, 1)} pts")
        return "\n".join(parts)

    def _reasoning_zh(self, blueprint: Blueprint, scores: Dict[str, float]) -> str:
        parts = []
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
            abundant = [RESOURCES_EN_TO_ZH.get(k, k) for k in blueprint.inputs.keys()]
            if abundant:
                parts.append(f"资源充足: +{int(scores['resource'])}分 ({', '.join(abundant)})")
        if scores['complexity_penalty'] > 0:
            parts.append(f"复杂度惩罚: -{int(scores['complexity_penalty'])}分 (复杂度{blueprint.complexity}×4)")
        total = scores['base_value'] + scores['synergy'] + scores['resource'] - scores['complexity_penalty']
        parts.append(f"总分: {round(total, 1)}分")
        return "\n".join(parts)
