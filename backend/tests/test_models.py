"""
Unit tests for data models and blueprint loader
"""
import pytest
import json
import tempfile
import os
from app.models import Blueprint, BlueprintDataLoader, Box, GameState


class TestBlueprint:
    """Test Blueprint data model"""
    
    def test_valid_blueprint_creation(self):
        """Test creating a valid blueprint"""
        bp = Blueprint(
            name="测试蓝图",
            name_en="Test Blueprint",
            type="生产建筑",
            dlc="基础版",
            inputs={"木材": 5},
            outputs={"食物": 10},
            values={"food": 3, "fuel": 2, "resolve": 1},
            complexity=2,
            synergy={"species_preferences": ["人类"], "biome_bonuses": {}}
        )
        assert bp.name == "测试蓝图"
        assert bp.values["food"] == 3
        assert bp.complexity == 2
    
    def test_blueprint_values_validation_too_high(self):
        """Test blueprint values validation - value too high"""
        with pytest.raises(ValueError, match="food value must be between 0 and 5"):
            Blueprint(
                name="无效蓝图",
                name_en="Invalid",
                type="生产建筑",
                dlc="基础版",
                inputs={},
                outputs={},
                values={"food": 6, "fuel": 2, "resolve": 1},  # food > 5
                complexity=2,
                synergy={}
            )
    
    def test_blueprint_values_validation_negative(self):
        """Test blueprint values validation - negative value"""
        with pytest.raises(ValueError, match="fuel value must be between 0 and 5"):
            Blueprint(
                name="无效蓝图",
                name_en="Invalid",
                type="生产建筑",
                dlc="基础版",
                inputs={},
                outputs={},
                values={"food": 3, "fuel": -1, "resolve": 1},  # fuel < 0
                complexity=2,
                synergy={}
            )
    
    def test_blueprint_complexity_validation_too_high(self):
        """Test blueprint complexity validation - too high"""
        with pytest.raises(ValueError, match="complexity must be between 1 and 5"):
            Blueprint(
                name="无效蓝图",
                name_en="Invalid",
                type="生产建筑",
                dlc="基础版",
                inputs={},
                outputs={},
                values={"food": 3, "fuel": 2, "resolve": 1},
                complexity=6,  # complexity > 5
                synergy={}
            )
    
    def test_blueprint_complexity_validation_too_low(self):
        """Test blueprint complexity validation - too low"""
        with pytest.raises(ValueError, match="complexity must be between 1 and 5"):
            Blueprint(
                name="无效蓝图",
                name_en="Invalid",
                type="生产建筑",
                dlc="基础版",
                inputs={},
                outputs={},
                values={"food": 3, "fuel": 2, "resolve": 1},
                complexity=0,  # complexity < 1
                synergy={}
            )
    
    def test_blueprint_synergy_defaults(self):
        """Test blueprint synergy field defaults"""
        bp = Blueprint(
            name="测试蓝图",
            name_en="Test",
            type="生产建筑",
            dlc="基础版",
            inputs={},
            outputs={},
            values={"food": 3, "fuel": 2, "resolve": 1},
            complexity=2,
            synergy={}  # Empty synergy
        )
        assert "species_preferences" in bp.synergy
        assert "biome_bonuses" in bp.synergy
        assert bp.synergy["species_preferences"] == []
        assert bp.synergy["biome_bonuses"] == {}


class TestBlueprintDataLoader:
    """Test BlueprintDataLoader"""
    
    def test_load_valid_data(self):
        """Test loading valid blueprint data"""
        # Create temporary JSON file
        data = {
            "version": "1.0.0",
            "last_updated": "2024-01-15",
            "blueprints": [
                {
                    "name": "农场",
                    "name_en": "Farm",
                    "type": "生产建筑",
                    "dlc": "基础版",
                    "inputs": {"木材": 5},
                    "outputs": {"食物": 10},
                    "values": {"food": 4, "fuel": 2, "resolve": 1},
                    "complexity": 2,
                    "synergy": {"species_preferences": ["人类"], "biome_bonuses": {}}
                }
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)
            temp_path = f.name
        
        try:
            loader = BlueprintDataLoader(temp_path)
            blueprints = loader.load()
            
            assert len(blueprints) == 1
            assert "农场" in blueprints
            assert blueprints["农场"].name_en == "Farm"
            assert loader.version == "1.0.0"
        finally:
            os.unlink(temp_path)
    
    def test_load_file_not_found(self):
        """Test loading from non-existent file"""
        loader = BlueprintDataLoader("nonexistent.json")
        with pytest.raises(FileNotFoundError):
            loader.load()
    
    def test_load_invalid_json(self):
        """Test loading invalid JSON"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("{ invalid json }")
            temp_path = f.name
        
        try:
            loader = BlueprintDataLoader(temp_path)
            with pytest.raises(ValueError, match="Invalid JSON format"):
                loader.load()
        finally:
            os.unlink(temp_path)
    
    def test_load_missing_blueprints_key(self):
        """Test loading data without 'blueprints' key"""
        data = {"version": "1.0.0"}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump(data, f)
            temp_path = f.name
        
        try:
            loader = BlueprintDataLoader(temp_path)
            with pytest.raises(ValueError, match="Missing 'blueprints' key"):
                loader.load()
        finally:
            os.unlink(temp_path)
    
    def test_load_with_invalid_blueprint(self):
        """Test loading data with some invalid blueprints"""
        data = {
            "version": "1.0.0",
            "blueprints": [
                {
                    "name": "有效蓝图",
                    "name_en": "Valid",
                    "type": "生产建筑",
                    "dlc": "基础版",
                    "inputs": {},
                    "outputs": {},
                    "values": {"food": 3, "fuel": 2, "resolve": 1},
                    "complexity": 2,
                    "synergy": {}
                },
                {
                    "name": "无效蓝图",
                    # Missing required fields
                }
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)
            temp_path = f.name
        
        try:
            loader = BlueprintDataLoader(temp_path)
            blueprints = loader.load()
            
            # Should load only the valid blueprint
            assert len(blueprints) == 1
            assert "有效蓝图" in blueprints
        finally:
            os.unlink(temp_path)
    
    def test_get_blueprint(self):
        """Test getting blueprint by name"""
        data = {
            "version": "1.0.0",
            "blueprints": [
                {
                    "name": "农场",
                    "name_en": "Farm",
                    "type": "生产建筑",
                    "dlc": "基础版",
                    "inputs": {},
                    "outputs": {},
                    "values": {"food": 4, "fuel": 2, "resolve": 1},
                    "complexity": 2,
                    "synergy": {}
                }
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)
            temp_path = f.name
        
        try:
            loader = BlueprintDataLoader(temp_path)
            loader.load()
            
            bp = loader.get_blueprint("农场")
            assert bp is not None
            assert bp.name == "农场"
            
            bp_none = loader.get_blueprint("不存在")
            assert bp_none is None
        finally:
            os.unlink(temp_path)
    
    def test_get_blueprints_by_type(self):
        """Test getting blueprints by type"""
        data = {
            "version": "1.0.0",
            "blueprints": [
                {
                    "name": "农场",
                    "name_en": "Farm",
                    "type": "生产建筑",
                    "dlc": "基础版",
                    "inputs": {},
                    "outputs": {},
                    "values": {"food": 4, "fuel": 2, "resolve": 1},
                    "complexity": 2,
                    "synergy": {}
                },
                {
                    "name": "酒馆",
                    "name_en": "Tavern",
                    "type": "服务建筑",
                    "dlc": "基础版",
                    "inputs": {},
                    "outputs": {},
                    "values": {"food": 1, "fuel": 0, "resolve": 5},
                    "complexity": 2,
                    "synergy": {}
                }
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)
            temp_path = f.name
        
        try:
            loader = BlueprintDataLoader(temp_path)
            loader.load()
            
            production = loader.get_blueprints_by_type("生产建筑")
            assert len(production) == 1
            assert production[0].name == "农场"
            
            service = loader.get_blueprints_by_type("服务建筑")
            assert len(service) == 1
            assert service[0].name == "酒馆"
        finally:
            os.unlink(temp_path)


class TestGameState:
    """Test GameState data model"""
    
    def test_game_state_creation(self):
        """Test creating a game state"""
        state = GameState(
            available_blueprints=["农场", "矿场"],
            resources={"木材": 25, "石料": 15},
            species="人类",
            confidence={"blueprints": 0.85, "resources": 0.92}
        )
        assert len(state.available_blueprints) == 2
        assert state.resources["木材"] == 25
        assert state.species == "人类"
        assert state.confidence["blueprints"] == 0.85
