"""
Template matching service using OpenCV
"""
import cv2
import numpy as np
import os
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


@dataclass
class MatchResult:
    """Template match result"""
    template_name: str
    confidence: float
    location: Tuple[int, int]  # (x, y)


class TemplateMatcher:
    """Template matcher using OpenCV for icon recognition"""
    
    def __init__(self, templates_dir: Optional[str] = None):
        self.templates_dir = templates_dir or os.getenv("TEMPLATES_DIR", "app/data/templates")
        self.templates_cache: Dict[str, np.ndarray] = {}
        self.load_templates()
    
    def load_templates(self) -> None:
        """
        Load all template images from templates directory into cache
        
        Templates should be organized as:
        templates/
          blueprints/
            farm.png
            mine.png
          species/
            human.png
            elf.png
        """
        if not os.path.exists(self.templates_dir):
            logger.warning(f"Templates directory not found: {self.templates_dir}")
            return
        
        template_count = 0
        for root, dirs, files in os.walk(self.templates_dir):
            for file in files:
                if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                    template_path = os.path.join(root, file)
                    template_name = os.path.splitext(file)[0]
                    
                    # Include subdirectory in name (e.g., "blueprints/farm")
                    rel_path = os.path.relpath(template_path, self.templates_dir)
                    template_key = os.path.splitext(rel_path)[0].replace(os.sep, '/')
                    
                    try:
                        template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
                        if template is not None:
                            self.templates_cache[template_key] = template
                            template_count += 1
                        else:
                            logger.warning(f"Failed to load template: {template_path}")
                    except Exception as e:
                        logger.error(f"Error loading template {template_path}: {e}")
        
        logger.info(f"Loaded {template_count} templates from {self.templates_dir}")
    
    def match_template(
        self,
        image: np.ndarray,
        template_name: str,
        threshold: float = 0.7,
        multi_scale: bool = True
    ) -> Optional[MatchResult]:
        """
        Match a single template in the image
        
        Args:
            image: Input image (BGR or grayscale)
            template_name: Name of template to match
            threshold: Confidence threshold (0-1)
            multi_scale: Whether to use multi-scale matching
        
        Returns:
            MatchResult if found, None otherwise
        """
        if template_name not in self.templates_cache:
            logger.warning(f"Template not found: {template_name}")
            return None
        
        template = self.templates_cache[template_name]
        
        # Convert image to grayscale if needed
        if len(image.shape) == 3:
            gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray_image = image
        
        if multi_scale:
            confidence, location = self._multi_scale_match(gray_image, template)
        else:
            result = cv2.matchTemplate(gray_image, template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            confidence = max_val
            location = max_loc
        
        if confidence >= threshold:
            return MatchResult(
                template_name=template_name,
                confidence=float(confidence),
                location=location
            )
        
        return None
    
    def match_multiple(
        self,
        image: np.ndarray,
        template_names: List[str],
        threshold: float = 0.7
    ) -> List[MatchResult]:
        """
        Match multiple templates in the image
        
        Args:
            image: Input image
            template_names: List of template names to match
            threshold: Confidence threshold
        
        Returns:
            List of MatchResult objects for all matches found
        """
        results = []
        
        for template_name in template_names:
            match = self.match_template(image, template_name, threshold)
            if match:
                results.append(match)
        
        return results
    
    def match_best(
        self,
        image: np.ndarray,
        template_names: List[str],
        threshold: float = 0.7
    ) -> Optional[MatchResult]:
        """
        Find the best matching template from a list
        
        Args:
            image: Input image
            template_names: List of template names to try
            threshold: Confidence threshold
        
        Returns:
            Best MatchResult or None
        """
        matches = self.match_multiple(image, template_names, threshold)
        
        if not matches:
            return None
        
        # Return match with highest confidence
        return max(matches, key=lambda m: m.confidence)
    
    def _multi_scale_match(
        self,
        image: np.ndarray,
        template: np.ndarray,
        scales: List[float] = [0.8, 0.9, 1.0, 1.1, 1.2]
    ) -> Tuple[float, Tuple[int, int]]:
        """
        Multi-scale template matching to handle size variations
        
        Args:
            image: Input image (grayscale)
            template: Template image (grayscale)
            scales: List of scale factors to try
        
        Returns:
            Tuple of (best_confidence, best_location)
        """
        best_confidence = 0.0
        best_location = (0, 0)
        best_scale = 1.0
        
        for scale in scales:
            # Resize template
            width = int(template.shape[1] * scale)
            height = int(template.shape[0] * scale)
            
            # Skip if scaled template is larger than image
            if width > image.shape[1] or height > image.shape[0]:
                continue
            
            resized_template = cv2.resize(template, (width, height))
            
            # Match template
            try:
                result = cv2.matchTemplate(image, resized_template, cv2.TM_CCOEFF_NORMED)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                
                if max_val > best_confidence:
                    best_confidence = max_val
                    best_location = max_loc
                    best_scale = scale
            except cv2.error as e:
                logger.debug(f"Template matching failed at scale {scale}: {e}")
                continue
        
        return best_confidence, best_location
    
    def get_available_templates(self) -> List[str]:
        """Get list of all available template names"""
        return list(self.templates_cache.keys())
    
    def get_template_count(self) -> int:
        """Get number of loaded templates"""
        return len(self.templates_cache)
