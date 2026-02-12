"""
Image analysis service for extracting game state from screenshots
"""
import cv2
import numpy as np
import re
from typing import List, Dict, Optional
import logging

from app.models import Box, GameState
from app.services.template_matcher import TemplateMatcher
from app.services.ocr_service import OCRService

logger = logging.getLogger(__name__)


def _slug(s: str) -> str:
    """与脚本中 slug 一致：建筑名 -> 模板文件名（无扩展）"""
    s = re.sub(r"[\s']+", "_", s)
    s = re.sub(r"[^a-zA-Z0-9_]", "", s)
    return s.lower() or "unknown"


class ImageAnalysisService:
    """Service for analyzing game screenshots and extracting game state"""
    
    def __init__(
        self,
        template_matcher: TemplateMatcher,
        ocr_service: OCRService,
        slug_to_blueprint_name: Optional[Dict[str, str]] = None,
        fallback_blueprints: Optional[List[str]] = None,
        fallback_resources: Optional[Dict[str, int]] = None,
    ):
        """
        Args:
            template_matcher: Template matcher instance
            ocr_service: OCR service instance
            slug_to_blueprint_name: 模板 slug -> 蓝图名（与 blueprints_data 的 name 一致）
            fallback_blueprints: 识别失败时返回的蓝图名列表
            fallback_resources: 识别失败时返回的资源字典
        """
        self.template_matcher = template_matcher
        self.ocr_service = ocr_service
        self.slug_to_blueprint_name = slug_to_blueprint_name or {}
        self.fallback_blueprints = fallback_blueprints or ["Woodcutters' Camp", "Bakery", "Tavern"]
        self.fallback_resources = fallback_resources or {"Wood": 25, "Planks": 15, "Stone": 10}
    
    def analyze_screenshot(
        self,
        image_path: str,
        boxes: List[Box]
    ) -> GameState:
        """
        Analyze screenshot and extract game state
        
        Args:
            image_path: Path to screenshot file
            boxes: List of recognition boxes defining regions of interest
        
        Returns:
            GameState object with extracted information
        """
        # Load image
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Failed to load image: {image_path}")
        
        # Initialize game state components
        available_blueprints = []
        resources = {}
        species = "未知"
        confidence = {}
        
        # Process each box
        for box in boxes:
            # Extract region of interest
            roi = image[
                box.y:box.y + box.height,
                box.x:box.x + box.width
            ]
            
            if box.label == 'blueprints':
                available_blueprints, conf = self._extract_blueprints(roi)
                confidence['blueprints'] = conf
            
            elif box.label == 'resources':
                resources, conf = self._extract_resources(roi)
                confidence['resources'] = conf
            
            elif box.label == 'species':
                species, conf = self._extract_species(roi)
                confidence['species'] = conf
        
        return GameState(
            available_blueprints=available_blueprints,
            resources=resources,
            species=species,
            confidence=confidence
        )
    
    def _extract_blueprints(
        self,
        image: np.ndarray
    ) -> tuple[List[str], float]:
        """
        Extract available blueprints from image region
        
        Args:
            image: Image region containing blueprints
        
        Returns:
            Tuple of (blueprint_names, confidence)
        """
        # Get all blueprint templates
        blueprint_templates = [
            t for t in self.template_matcher.get_available_templates()
            if t.startswith('blueprints/')
        ]
        
        if not blueprint_templates:
            logger.warning("No blueprint templates available, using fallback")
            return self.fallback_blueprints, 0.5
        
        matches = self.template_matcher.match_multiple(
            image,
            blueprint_templates,
            threshold=0.6
        )
        
        if not matches:
            logger.info("No blueprint templates matched, using fallback")
            return self.fallback_blueprints, 0.5
        
        blueprint_names = []
        total_confidence = 0.0
        for match in matches:
            template_slug = match.template_name.split('/')[-1]
            # 优先用当前加载的蓝图名（与 blueprints_data 的 name 一致）
            name = self.slug_to_blueprint_name.get(template_slug) or self._map_blueprint_name(template_slug)
            blueprint_names.append(name)
            total_confidence += match.confidence
        
        avg_confidence = total_confidence / len(matches) if matches else 0.0
        return blueprint_names, avg_confidence
    
    def _extract_resources(
        self,
        image: np.ndarray
    ) -> tuple[Dict[str, int], float]:
        """
        Extract resource inventory from image region
        
        Args:
            image: Image region containing resources
        
        Returns:
            Tuple of (resources_dict, confidence)
        """
        resources = {}
        
        # Try OCR to extract numbers
        if self.ocr_service.is_available():
            # Split image into rows/columns for different resources
            # This is a simplified approach
            height, width = image.shape[:2]
            
            # Try to extract numbers from different regions
            # 资源名与 fallback_resources 一致（ATS 用英文）
            resource_names = list(self.fallback_resources.keys()) if self.fallback_resources else ["Wood", "Planks", "Stone"]
            step = max(1, height // max(1, len(resource_names)))
            regions = [
                (resource_names[i], image[i * step:(i + 1) * step, :])
                for i in range(min(len(resource_names), 3))
            ]
            
            total_confidence = 0.0
            successful_extractions = 0
            
            for resource_name, region in regions:
                number = self.ocr_service.extract_number(region)
                if number is not None:
                    resources[resource_name] = number
                    total_confidence += 0.8
                    successful_extractions += 1
            
            if successful_extractions > 0:
                avg_confidence = total_confidence / successful_extractions
                return resources, avg_confidence
        
        logger.info("OCR not available or failed, using fallback resources")
        return dict(self.fallback_resources), 0.5
    
    def _extract_species(
        self,
        image: np.ndarray
    ) -> tuple[str, float]:
        """
        Extract current species from image region
        
        Args:
            image: Image region containing species indicator
        
        Returns:
            Tuple of (species_name, confidence)
        """
        # Get species templates
        species_templates = [
            t for t in self.template_matcher.get_available_templates()
            if t.startswith('species/')
        ]
        
        if not species_templates:
            logger.warning("No species templates available, using fallback")
            return self._get_fallback_species(), 0.5
        
        # Find best matching species
        match = self.template_matcher.match_best(
            image,
            species_templates,
            threshold=0.6
        )
        
        if match:
            # 内部统一英文：模板名 human -> Human
            template_name = match.template_name.split('/')[-1]
            species_name = template_name.capitalize() if template_name else "Human"
            return species_name, match.confidence
        
        logger.info("No species template matched, using fallback")
        return self._get_fallback_species(), 0.5
    
    def _map_blueprint_name(self, english_name: str) -> str:
        """Map English blueprint name to Chinese"""
        mapping = {
            'farm': '农场',
            'mine': '矿场',
            'kiln': '窑',
            'bakery': '面包房',
            'smithy': '铁匠铺',
            'tavern': '酒馆',
            'temple': '神殿',
            'workshop': '工坊',
            'apothecary': '药剂铺',
            'lumber_mill': '伐木场',
            'fishery': '渔场',
            'hunting_lodge': '狩猎小屋',
            'mill': '磨坊',
            'alchemy_workshop': '炼金工坊',
            'forge': '锻造厂',
            'library': '图书馆',
            'training_ground': '训练场',
            'market': '市场',
            'barracks': '兵营',
            'quarry': '采石场',
            'weaver': '织布坊',
            'pottery': '陶器作坊',
            'ranch': '牧场'
        }
        return mapping.get(english_name, english_name)
    
    def _map_species_name(self, english_name: str) -> str:
        """Map English species name to Chinese (含 Against the Storm 五种族)"""
        mapping = {
            'human': '人类',
            'beaver': '海狸',
            'harpy': '鹰身人',
            'lizard': '蜥蜴人',
            'fox': '狐狸',
            'elf': '精灵',
            'dwarf': '矮人',
            'orc': '兽人',
        }
        return mapping.get(english_name.lower(), english_name)
    
    def _get_fallback_species(self) -> str:
        """Get fallback species when recognition fails（内部英文）"""
        return "Human"
