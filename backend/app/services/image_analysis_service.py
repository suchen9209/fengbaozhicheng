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
        self.fallback_blueprints = fallback_blueprints or ["伐木场", "面包房", "酒馆"]
        # 使用中文资源名，与 blueprints_data.json 一致
        self.fallback_resources = fallback_resources or {"木材": 25, "石料": 15, "食物": 30}
        
        # 常见资源名称列表（用于 OCR 后的文本匹配）
        self.resource_names = ["木材", "石料", "食物", "水", "黏土", "谷物", "草料", 
                              "矿石", "煤炭", "金属锭", "砖块", "陶器", "皮革", "羊毛",
                              "布料", "工具", "武器", "药剂", "纸张", "鱼", "肉", 
                              "面粉", "面包", "草药", "魔法精华"]
    
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
        
        Uses a two-step approach:
        1. Detect resource icon positions (if resource templates exist)
        2. OCR to extract numbers from regions next to icons
        
        Args:
            image: Image region containing resources
        
        Returns:
            Tuple of (resources_dict, confidence)
        """
        resources = {}
        
        if not self.ocr_service.is_available():
            logger.info("OCR not available, using fallback resources")
            return dict(self.fallback_resources), 0.5
        
        try:
            height, width = image.shape[:2]
            
            # Strategy: Resources are typically displayed as [Icon] [Number] pairs
            # We'll scan the image for numbers and associate them with nearby text/icons
            
            # Convert to grayscale for processing
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()
            
            # Method 1: Try to find number regions using contour detection
            # Resources typically show numbers in consistent positions
            numbers_found = self._extract_numbers_from_regions(gray)
            
            # If we found numbers, try to associate them with resource names
            if numbers_found:
                # For now, map found numbers to most common resources
                # In a more advanced version, we'd detect resource icons
                for i, (number, confidence) in enumerate(numbers_found[:len(self.fallback_resources)]):
                    if i < len(self.fallback_resources):
                        resource_name = list(self.fallback_resources.keys())[i]
                        resources[resource_name] = number
                
                avg_confidence = sum(conf for _, conf in numbers_found[:len(resources)]) / len(resources) if resources else 0.5
                return resources, avg_confidence
            
            # Method 2: Divide image into horizontal strips (for vertical resource lists)
            min_resources = min(3, len(self.fallback_resources))
            step = max(1, height // min_resources)
            
            total_confidence = 0.0
            successful_extractions = 0
            
            for i, resource_name in enumerate(list(self.fallback_resources.keys())[:min_resources]):
                y_start = i * step
                y_end = min((i + 1) * step, height)
                region = image[y_start:y_end, :]
                
                if region.size == 0:
                    continue
                
                number = self.ocr_service.extract_number(region)
                if number is not None:
                    resources[resource_name] = number
                    total_confidence += 0.8
                    successful_extractions += 1
            
            if successful_extractions > 0:
                avg_confidence = total_confidence / successful_extractions
                return resources, avg_confidence
            
        except Exception as e:
            logger.error(f"Resource extraction failed: {e}")
        
        logger.info("Resource extraction failed, using fallback resources")
        return dict(self.fallback_resources), 0.5
    
    def _extract_numbers_from_regions(
        self,
        gray_image: np.ndarray
    ) -> list[tuple[int, float]]:
        """
        Extract numbers from different regions of the image
        
        Args:
            gray_image: Grayscale image
            
        Returns:
            List of (number, confidence) tuples
        """
        numbers_found = []
        height, width = gray_image.shape
        
        # Divide image into a grid and try OCR on each cell
        rows, cols = 3, 2  # 3 rows, 2 columns (icon + number)
        cell_h, cell_w = height // rows, width // cols
        
        for row in range(rows):
            for col in range(cols):
                y1, y2 = row * cell_h, min((row + 1) * cell_h, height)
                x1, x2 = col * cell_w, min((col + 1) * cell_w, width)
                
                cell = gray_image[y1:y2, x1:x2]
                if cell.size == 0:
                    continue
                
                number = self.ocr_service.extract_number(cell)
                if number is not None and 0 <= number <= 9999:  # Reasonable resource range
                    numbers_found.append((number, 0.7))
        
        return numbers_found
    
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
