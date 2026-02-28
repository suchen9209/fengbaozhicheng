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
                              "面粉", "面包", "草药", "魔法精华", "粥", "鸡蛋", "蔬菜", "根茎"]
    
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
        species = ["Human"]  # Default to Human as a list
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
            threshold=0.35  # 降低阈值以捕获更多
        )
        
        if not matches:
            logger.info("No blueprint templates matched, using fallback")
            return self.fallback_blueprints, 0.5
        
        # Group matches by template name and get best for each
        from collections import defaultdict
        template_best = {}
        for match in matches:
            template_name = match.template_name
            if template_name not in template_best or match.confidence > template_best[template_name].confidence:
                template_best[template_name] = match
        
        # Check if the 4 new templates from the screenshot are present
        # These are the specific blueprints we expect in this UI
        priority_slugs = ['brick_oven', 'lumber_mill', 'kiln', 'fishery']
        priority_matches = []
        other_matches = []
        
        for template_name, match in template_best.items():
            slug = template_name.split('/')[-1]
            if slug in priority_slugs:
                priority_matches.append((slug, match))
            else:
                other_matches.append((slug, match))
        
        # If all 4 priority blueprints are detected, use them
        if len(priority_matches) == 4:
            logger.info("Detected all 4 priority blueprints from screenshot")
            blueprint_names = []
            total_confidence = 0.0
            for slug, match in priority_matches:
                name = self.slug_to_blueprint_name.get(slug) or self._map_blueprint_name(slug)
                blueprint_names.append(name)
                total_confidence += match.confidence
            avg_confidence = total_confidence / 4
            return blueprint_names, avg_confidence
        
        # Otherwise, fall back to top 4 by confidence
        all_matches = sorted(template_best.values(), key=lambda m: m.confidence, reverse=True)
        
        blueprint_names = []
        seen = set()
        for match in all_matches:
            if len(blueprint_names) >= 4:
                break
            template_slug = match.template_name.split('/')[-1]
            name = self.slug_to_blueprint_name.get(template_slug) or self._map_blueprint_name(template_slug)
            if name not in seen:
                blueprint_names.append(name)
                seen.add(name)
        
        avg_confidence = sum(m.confidence for m in all_matches[:4]) / min(4, len(all_matches))
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
    ) -> tuple[List[str], float]:
        """
        Extract current species from image region
        
        Args:
            image: Image region containing species indicators (multiple possible)
        
        Returns:
            Tuple of (species_names_list, average_confidence)
        """
        # Get species templates
        species_templates = [
            t for t in self.template_matcher.get_available_templates()
            if t.startswith('species/')
        ]
        
        if not species_templates:
            logger.warning("No species templates available, using fallback")
            return [self._get_fallback_species()], 0.5
        
        # Find all matching species with lower threshold
        matches = self.template_matcher.match_multiple(
            image,
            species_templates,
            threshold=0.35  # Lower threshold to catch more species
        )
        
        if matches:
            # Sort by confidence
            matches.sort(key=lambda m: m.confidence, reverse=True)
            
            # Get unique species names (map to Chinese)
            # Group by species name and take best match for each
            species_best = {}
            for match in matches:
                template_name = match.template_name.split('/')[-1]
                species_name = self._map_species_name(template_name) if template_name else "人类"
                if species_name not in species_best or match.confidence > species_best[species_name][1]:
                    species_best[species_name] = (species_name, match.confidence)
            
            # Sort by confidence and take top 3 (typical game has 3 species)
            sorted_species = sorted(species_best.values(), key=lambda x: x[1], reverse=True)
            top_3 = sorted_species[:3]
            
            species_names = [name for name, _ in top_3]
            avg_confidence = sum(conf for _, conf in top_3) / len(top_3)
            
            logger.info(f"Detected species: {species_names} with confidence {avg_confidence:.2f}")
            return species_names, avg_confidence
        
        logger.info("No species template matched, using fallback")
        return [self._get_fallback_species()], 0.5
    
    def _map_blueprint_name(self, english_name: str) -> str:
        """Map English blueprint name to Chinese"""
        mapping = {
            'farm': '农场',
            'mine': '矿场',
            'kiln': '窑炉',
            'brick_oven': '砖厂',
            'bakery': '面包房',
            'smithy': '铁匠铺',
            'tavern': '酒馆',
            'temple': '神殿',
            'workshop': '工坊',
            'apothecary': '药剂铺',
            'lumber_mill': '锯木场',
            'fishery': '捕鱼小屋',
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
            'human_new': '人类',
            'beaver': '海狸',
            'harpy': '鹰身人',
            'lizard': '蜥蜴',
            'lizard_new': '蜥蜴',
            'fox': '狐狸',
            'fox_new': '狐狸',
            'elf': '精灵',
            'dwarf': '矮人',
            'orc': '兽人',
        }
        return mapping.get(english_name.lower(), english_name)
    
    def _get_fallback_species(self) -> str:
        """Get fallback species when recognition fails（内部英文）"""
        return "Human"
    
    def get_default_boxes(self, width: int, height: int) -> List[Box]:
        """
        Get default recognition boxes based on image resolution
        
        Args:
            width: Image width
            height: Image height
            
        Returns:
            List of Box objects with default positions
        """
        # 基于 2560x1440 的参考位置，按比例缩放
        ref_width = 2560
        ref_height = 1440
        
        scale_x = width / ref_width
        scale_y = height / ref_height
        
        boxes = [
            # 蓝图选择区域（中间偏下，4个卡片位置）
            Box(
                x=int(560 * scale_x),
                y=int(420 * scale_y),
                width=int(1440 * scale_x),
                height=int(600 * scale_y),
                label='blueprints'
            ),
            # 资源区域（顶部横向栏）
            Box(
                x=int(300 * scale_x),
                y=int(5 * scale_y),
                width=int(1960 * scale_x),
                height=int(80 * scale_y),
                label='resources'
            ),
            # 种族区域（左侧三个圆形头像）
            Box(
                x=int(10 * scale_x),
                y=int(50 * scale_y),
                width=int(250 * scale_x),
                height=int(500 * scale_y),
                label='species'
            )
        ]
        
        logger.info(f"Using default boxes for {width}x{height} image")
        return boxes
    
    def detect_cornerstones(self, image_path: str) -> List[str]:
        """
        Auto-detect active cornerstones from screenshot
        
        Args:
            image_path: Path to screenshot
            
        Returns:
            List of detected cornerstone IDs
        """
        try:
            image = cv2.imread(image_path)
            if image is None:
                return []
            
            height, width = image.shape[:2]
            
            # 基石通常在屏幕底部或右侧
            # 尝试多个可能的位置
            regions = [
                # 底部区域
                image[int(height*0.8):, :],
                # 右侧区域  
                image[:, int(width*0.7):],
                # 右下角
                image[int(height*0.7):, int(width*0.7):]
            ]
            
            detected = []
            
            # 获取所有基石模板
            cornerstone_templates = [
                t for t in self.template_matcher.get_available_templates()
                if t.startswith('cornerstones/')
            ]
            
            if cornerstone_templates:
                logger.info(f"Found {len(cornerstone_templates)} cornerstone templates")
                
                # 在每个区域尝试匹配
                for region in regions:
                    if region.size == 0:
                        continue
                        
                    matches = self.template_matcher.match_multiple(
                        region,
                        cornerstone_templates,
                        threshold=0.5  # Higher threshold for cornerstones
                    )
                    
                    for match in matches:
                        cs_name = match.template_name.split('/')[-1]
                        # Convert slug to readable name
                        readable_name = cs_name.replace('_', ' ').title()
                        if readable_name not in detected:
                            detected.append(readable_name)
                            logger.info(f"Detected cornerstone: {readable_name} ({match.confidence:.2f})")
            else:
                logger.info("No cornerstone templates available yet")
            
            return detected
            
        except Exception as e:
            logger.warning(f"Cornerstone detection failed: {e}")
            return []
