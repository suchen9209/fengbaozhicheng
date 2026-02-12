"""
Unit tests for RecommendationEngine
"""
import pytest
from app.services.recommendation_engine import RecommendationEngine
from app.models import Blueprint, GameState


@pytest.fixture
def sample_blueprints():
    """Create sample blueprints for testing"""
    return {
        "农场": Blueprint(
            name="农场",
            name_en="Farm",
            type="生产建筑",
            dlc="基础版",
            inputs={"木材": 5, "石料": 3},
            outputs={"食物": 10},
            values={"food": 4, "fuel": 2, "resolve": 1},
            complexity=2,
            synergy={"species_preferences": ["人类", "精灵"], "biome_bonuses": {}}
        ),
        "矿场": Blueprint(
            name="矿场",
            name_en="Mine",
            type="生产建筑",
            dlc="基础版",
            inputs={"木材": 8},
            outputs={"石料": 15},
            values={"food": 0, "fuel": 3, "resolve": 2},
            complexity=3,
            synergy={"species_preferences": ["矮人"], "biome_bonuses": {}}
        ),
        "酒馆": Blueprint(
            name="酒馆",
            name_en="Tavern",
            type="服务建筑",
            dlc="基础版",
            inputs={"食物": 5, "木材": 3},
            outputs={},
            values={"food": 1, "fuel": 0, "resolve": 5},
            complexity=2,
            synergy={"species_preferences": ["人类", "矮人"], "biome_bonuses": {}}
        )
    }


@pytest.fixture
def sample_game_state():
    """Create sample game state"""
    return GameState(
        available_blueprints=["农场", "矿场", "酒馆"],
        resources={"木材": 25, "石料": 15, "食物": 30},
        species="人类",
        confidence={"blueprints": 0.85}
    )


class TestRecommendationEngine:
    """Test RecommendationEngine"""
    
    def test_base_value_score_calculation(self, sample_blueprints):
        """Test base value score calculation: food×10 + fuel×8 + resolve×12"""
        engine = RecommendationEngine(sample_blueprints)
        
        # Test 农场: food=4, fuel=2, resolve=1
        # Expected: 4*10 + 2*8 + 1*12 = 40 + 16 + 12 = 68
        score = engine._calculate_base_value_score(sample_blueprints["农场"])
        assert score == 68
        
        # Test 矿场: food=0, fuel=3, resolve=2
        # Expected: 0*10 + 3*8 + 2*12 = 0 + 24 + 24 = 48
        score = engine._calculate_base_value_score(sample_blueprints["矿场"])
        assert score == 48
        
        # Test 酒馆: food=1, fuel=0, resolve=5
        # Expected: 1*10 + 0*8 + 5*12 = 10 + 0 + 60 = 70
        score = engine._calculate_base_value_score(sample_blueprints["酒馆"])
        assert score == 70
    
    def test_synergy_score_matching_species(self, sample_blueprints):
        """Test synergy score when species matches"""
        engine = RecommendationEngine(sample_blueprints)
        
        # 农场 prefers 人类
        score = engine._calculate_synergy_score(sample_blueprints["农场"], "人类")
        assert score == 5.0
        
        # 酒馆 prefers 人类
        score = engine._calculate_synergy_score(sample_blueprints["酒馆"], "人类")
        assert score == 5.0
    
    def test_synergy_score_non_matching_species(self, sample_blueprints):
        """Test synergy score when species doesn't match"""
        engine = RecommendationEngine(sample_blueprints)
        
        # 矿场 prefers 矮人, not 人类
        score = engine._calculate_synergy_score(sample_blueprints["矿场"], "人类")
        assert score == 0.0
        
        # 农场 prefers 人类/精灵, not 矮人
        score = engine._calculate_synergy_score(sample_blueprints["农场"], "矮人")
        assert score == 0.0
    
    def test_resource_score_abundant(self, sample_blueprints):
        """Test resource score when resources are abundant"""
        engine = RecommendationEngine(sample_blueprints)
        
        resources = {"木材": 25, "石料": 15, "食物": 30}
        
        # 农场 needs 木材 and 石料, both abundant (>=10)
        # Expected: 2 resources * 3 = 6
        score = engine._calculate_resource_score(sample_blueprints["农场"], resources)
        assert score == 6.0
        
        # 酒馆 needs 食物 and 木材, both abundant
        # Expected: 2 resources * 3 = 6
        score = engine._calculate_resource_score(sample_blueprints["酒馆"], resources)
        assert score == 6.0
    
    def test_resource_score_scarce(self, sample_blueprints):
        """Test resource score when resources are scarce"""
        engine = RecommendationEngine(sample_blueprints)
        
        resources = {"木材": 5, "石料": 3}  # Both < 10
        
        # 农场 needs 木材 and 石料, both scarce
        # Expected: 0
        score = engine._calculate_resource_score(sample_blueprints["农场"], resources)
        assert score == 0.0
    
    def test_resource_score_partial(self, sample_blueprints):
        """Test resource score when some resources are abundant"""
        engine = RecommendationEngine(sample_blueprints)
        
        resources = {"木材": 25, "石料": 5}  # 木材 abundant, 石料 scarce
        
        # 农场 needs 木材 (abundant) and 石料 (scarce)
        # Expected: 1 resource * 3 = 3
        score = engine._calculate_resource_score(sample_blueprints["农场"], resources)
        assert score == 3.0
    
    def test_complexity_penalty(self, sample_blueprints):
        """Test complexity penalty calculation: complexity × 4"""
        engine = RecommendationEngine(sample_blueprints)
        
        # 农场: complexity=2, penalty=2*4=8
        penalty = engine._calculate_complexity_penalty(sample_blueprints["农场"])
        assert penalty == 8.0
        
        # 矿场: complexity=3, penalty=3*4=12
        penalty = engine._calculate_complexity_penalty(sample_blueprints["矿场"])
        assert penalty == 12.0
    
    def test_calculate_score(self, sample_blueprints, sample_game_state):
        """Test complete score calculation"""
        engine = RecommendationEngine(sample_blueprints)
        
        # Test 农场 with 人类
        # Base: 68, Synergy: 5, Resource: 6, Penalty: 8
        # Total: 68 + 5 + 6 - 8 = 71
        score, reasoning = engine._calculate_score(
            sample_blueprints["农场"],
            sample_game_state
        )
        assert score == 71.0
        assert "基础价值分: 68分" in reasoning
        assert "种族协同: +5分" in reasoning
        assert "资源充足: +6分" in reasoning
        assert "复杂度惩罚: -8分" in reasoning
        assert "总分: 71.0分" in reasoning
    
    def test_generate_recommendations(self, sample_blueprints, sample_game_state):
        """Test generating recommendations"""
        engine = RecommendationEngine(sample_blueprints)
        
        recommendations = engine.generate_recommendations(
            sample_game_state,
            ["农场", "矿场", "酒馆"],
            top_k=3
        )
        
        # Should return 3 recommendations
        assert len(recommendations) == 3
        
        # Should be sorted by score descending
        assert recommendations[0].score >= recommendations[1].score
        assert recommendations[1].score >= recommendations[2].score
        
        # Ranks should be 1, 2, 3
        assert recommendations[0].rank == 1
        assert recommendations[1].rank == 2
        assert recommendations[2].rank == 3
        
        # Each should have details
        for rec in recommendations:
            assert rec.blueprint_name is not None
            assert rec.score > 0
            assert rec.reasoning is not None
            assert rec.details is not None
    
    def test_generate_recommendations_top_k(self, sample_blueprints, sample_game_state):
        """Test top_k parameter"""
        engine = RecommendationEngine(sample_blueprints)
        
        # Request only top 2
        recommendations = engine.generate_recommendations(
            sample_game_state,
            ["农场", "矿场", "酒馆"],
            top_k=2
        )
        
        assert len(recommendations) == 2
    
    def test_generate_recommendations_unknown_blueprint(self, sample_blueprints, sample_game_state):
        """Test handling unknown blueprints"""
        engine = RecommendationEngine(sample_blueprints)
        
        # Include an unknown blueprint
        recommendations = engine.generate_recommendations(
            sample_game_state,
            ["农场", "未知蓝图", "矿场"],
            top_k=5
        )
        
        # Should only return recommendations for known blueprints
        assert len(recommendations) == 2
        assert all(rec.blueprint_name in ["农场", "矿场"] for rec in recommendations)
    
    def test_recommendation_sorting(self, sample_blueprints):
        """Test that recommendations are sorted correctly"""
        engine = RecommendationEngine(sample_blueprints)
        
        # Create game state that favors 酒馆 (high resolve value + synergy)
        game_state = GameState(
            available_blueprints=["农场", "矿场", "酒馆"],
            resources={"木材": 25, "食物": 30},
            species="人类",
            confidence={}
        )
        
        recommendations = engine.generate_recommendations(
            game_state,
            ["农场", "矿场", "酒馆"],
            top_k=3
        )
        
        # 酒馆 should rank high due to high resolve value (5*12=60) + synergy (5)
        # Find 酒馆 in recommendations
        tavern_rec = next(r for r in recommendations if r.blueprint_name == "酒馆")
        
        # 酒馆 should be in top 2
        assert tavern_rec.rank <= 2


class TestEdgeCases:
    """Test edge cases"""
    
    def test_empty_available_blueprints(self, sample_blueprints, sample_game_state):
        """Test with no available blueprints"""
        engine = RecommendationEngine(sample_blueprints)
        
        recommendations = engine.generate_recommendations(
            sample_game_state,
            [],
            top_k=5
        )
        
        assert len(recommendations) == 0
    
    def test_blueprint_with_no_inputs(self):
        """Test blueprint with no input requirements"""
        blueprint = Blueprint(
            name="测试",
            name_en="Test",
            type="生产建筑",
            dlc="基础版",
            inputs={},  # No inputs
            outputs={"木材": 10},
            values={"food": 0, "fuel": 3, "resolve": 0},
            complexity=1,
            synergy={}
        )
        
        engine = RecommendationEngine({"测试": blueprint})
        
        # Should not crash with empty inputs
        score = engine._calculate_resource_score(blueprint, {"木材": 100})
        assert score == 0.0  # No inputs, so no resource bonus
    
    def test_zero_values_blueprint(self):
        """Test blueprint with all zero values"""
        blueprint = Blueprint(
            name="测试",
            name_en="Test",
            type="生产建筑",
            dlc="基础版",
            inputs={},
            outputs={},
            values={"food": 0, "fuel": 0, "resolve": 0},
            complexity=1,
            synergy={}
        )
        
        engine = RecommendationEngine({"测试": blueprint})
        
        score = engine._calculate_base_value_score(blueprint)
        assert score == 0.0
