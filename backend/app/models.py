"""
Data models for Stormgate Blueprint Assistant
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import os
from pathlib import Path


@dataclass
class Blueprint:
    """Blueprint data model"""
    name: str
    name_en: str
    type: str
    dlc: str
    inputs: Dict[str, int]
    outputs: Dict[str, int]
    values: Dict[str, int]  # food, fuel, resolve (0-5)
    complexity: int  # 1-5
    synergy: Dict[str, Any]  # species_preferences, biome_bonuses
    description: str = ""

    def __post_init__(self):
        """Validate blueprint data after initialization"""
        # Validate values range (0-5)
        for key in ['food', 'fuel', 'resolve']:
            if key in self.values:
                value = self.values[key]
                if not (0 <= value <= 5):
                    raise ValueError(f"Blueprint {self.name}: {key} value must be between 0 and 5, got {value}")
        
        # Validate complexity range (1-5)
        if not (1 <= self.complexity <= 5):
            raise ValueError(f"Blueprint {self.name}: complexity must be between 1 and 5, got {self.complexity}")
        
        # Validate required fields in synergy
        if 'species_preferences' not in self.synergy:
            self.synergy['species_preferences'] = []
        if 'biome_bonuses' not in self.synergy:
            self.synergy['biome_bonuses'] = {}


@dataclass
class Box:
    """Recognition box coordinates"""
    x: int
    y: int
    width: int
    height: int
    label: str  # 'blueprints' | 'resources' | 'species'


@dataclass
class GameState:
    """Game state extracted from screenshot"""
    available_blueprints: List[str]
    resources: Dict[str, int]
    species: List[str]  # Changed from str to List[str] to support multiple species
    confidence: Dict[str, float] = field(default_factory=dict)
    
    def has_resources_for(self, blueprint: 'Blueprint') -> bool:
        """
        Check if current resources are sufficient to build the blueprint
        
        Args:
            blueprint: Blueprint to check
            
        Returns:
            True if all required resources are available in sufficient quantity
        """
        for resource_name, required_amount in blueprint.inputs.items():
            available = self.resources.get(resource_name, 0)
            if available < required_amount:
                return False
        return True
    
    def get_missing_resources(self, blueprint: 'Blueprint') -> Dict[str, Dict[str, int]]:
        """
        Get details of missing resources for a blueprint
        
        Returns:
            Dict mapping resource name to {required, available, missing}
        """
        missing = {}
        for resource_name, required_amount in blueprint.inputs.items():
            available = self.resources.get(resource_name, 0)
            if available < required_amount:
                missing[resource_name] = {
                    'required': required_amount,
                    'available': available,
                    'missing': required_amount - available
                }
        return missing


@dataclass
class Recommendation:
    """Blueprint recommendation with score and reasoning"""
    blueprint_name: str
    score: float
    rank: int
    reasoning: str
    details: Blueprint
    buildable: bool = False
    missing_resources: Dict[str, Dict[str, int]] = field(default_factory=dict)
    cornerstone_bonus: float = 1.0  # 基石加成倍数
    recommended_cornerstones: List[str] = field(default_factory=list)  # 推荐的基石


@dataclass
class AnalysisRecord:
    """Analysis record for history"""
    id: str
    timestamp: datetime
    screenshot_path: str
    game_state: GameState
    recommendations: List[Recommendation]
    user_id: Optional[str] = None
    session_id: str = ""


class BlueprintDataLoader:
    """Loader for blueprint data from JSON file"""
    
    def __init__(self, data_path: str = "app/data/blueprints_data.json"):
        self.data_path = data_path
        self.blueprints: Dict[str, Blueprint] = {}
        self.version: str = ""
        self.last_updated: str = ""
    
    def load(self) -> Dict[str, Blueprint]:
        """
        Load blueprint data from JSON file
        
        Returns:
            Dictionary mapping blueprint names to Blueprint objects
        
        Raises:
            FileNotFoundError: If data file doesn't exist
            ValueError: If data format is invalid
            json.JSONDecodeError: If JSON is malformed
        """
        if not os.path.exists(self.data_path):
            raise FileNotFoundError(f"Blueprint data file not found: {self.data_path}")
        
        try:
            with open(self.data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format in {self.data_path}: {e}")
        
        # Validate top-level structure
        if 'blueprints' not in data:
            raise ValueError("Missing 'blueprints' key in data file")
        
        self.version = data.get('version', 'unknown')
        self.last_updated = data.get('last_updated', 'unknown')
        
        # Load and validate each blueprint
        blueprints = {}
        for bp_data in data['blueprints']:
            try:
                blueprint = self._parse_blueprint(bp_data)
                blueprints[blueprint.name] = blueprint
            except (KeyError, ValueError, TypeError) as e:
                # Log error but continue loading other blueprints
                print(f"Warning: Failed to load blueprint {bp_data.get('name', 'unknown')}: {e}")
                continue
        
        if not blueprints:
            raise ValueError("No valid blueprints loaded from data file")
        
        self.blueprints = blueprints
        return blueprints
    
    def _parse_blueprint(self, data: Dict[str, Any]) -> Blueprint:
        """
        Parse blueprint data from dictionary
        
        Args:
            data: Blueprint data dictionary
        
        Returns:
            Blueprint object
        
        Raises:
            KeyError: If required field is missing
            ValueError: If field value is invalid
        """
        # Validate required fields
        required_fields = ['name', 'type', 'dlc', 'inputs', 'outputs', 'values', 'complexity', 'synergy']
        for field in required_fields:
            if field not in data:
                raise KeyError(f"Missing required field: {field}")
        
        # Validate values structure
        values = data['values']
        if not isinstance(values, dict):
            raise ValueError("'values' must be a dictionary")
        
        required_value_keys = ['food', 'fuel', 'resolve']
        for key in required_value_keys:
            if key not in values:
                raise KeyError(f"Missing required value key: {key}")
            if not isinstance(values[key], int):
                raise ValueError(f"Value '{key}' must be an integer")
        
        # Validate complexity
        if not isinstance(data['complexity'], int):
            raise ValueError("'complexity' must be an integer")
        
        # Validate synergy structure
        synergy = data['synergy']
        if not isinstance(synergy, dict):
            raise ValueError("'synergy' must be a dictionary")
        
        # Create Blueprint object (validation happens in __post_init__)
        return Blueprint(
            name=data['name'],
            name_en=data.get('name_en', data['name']),
            type=data['type'],
            dlc=data['dlc'],
            inputs=data['inputs'],
            outputs=data['outputs'],
            values=values,
            complexity=data['complexity'],
            synergy=synergy,
            description=data.get('description', '')
        )
    
    def get_blueprint(self, name: str) -> Optional[Blueprint]:
        """Get blueprint by name"""
        return self.blueprints.get(name)
    
    def get_all_blueprints(self) -> List[Blueprint]:
        """Get all blueprints as a list"""
        return list(self.blueprints.values())
    
    def get_blueprints_by_type(self, blueprint_type: str) -> List[Blueprint]:
        """Get all blueprints of a specific type"""
        return [bp for bp in self.blueprints.values() if bp.type == blueprint_type]
    
    def get_info(self) -> Dict[str, Any]:
        """Get loader information"""
        return {
            "version": self.version,
            "last_updated": self.last_updated,
            "total_blueprints": len(self.blueprints),
            "data_path": self.data_path
        }
