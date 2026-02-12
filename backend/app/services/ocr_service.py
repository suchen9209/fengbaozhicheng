"""
OCR service using Tesseract
"""
import cv2
import numpy as np
import re
from typing import Optional
import logging

try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    logging.warning("pytesseract not available, OCR functionality will be limited")

logger = logging.getLogger(__name__)


class OCRService:
    """OCR service for text and number extraction"""
    
    def __init__(self, tesseract_cmd: Optional[str] = None):
        """
        Initialize OCR service
        
        Args:
            tesseract_cmd: Path to tesseract executable (optional)
        """
        self.available = TESSERACT_AVAILABLE
        
        if self.available and tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
        
        if not self.available:
            logger.warning("Tesseract OCR not available")
    
    def extract_text(
        self,
        image: np.ndarray,
        lang: str = 'chi_sim+eng',
        preprocess: bool = True
    ) -> str:
        """
        Extract text from image
        
        Args:
            image: Input image (BGR or grayscale)
            lang: OCR language (supports Chinese simplified + English)
            preprocess: Whether to preprocess image
        
        Returns:
            Extracted text string
        """
        if not self.available:
            logger.warning("OCR not available, returning empty string")
            return ""
        
        try:
            # Preprocess if requested
            if preprocess:
                processed = self._preprocess_image(image)
            else:
                processed = image
            
            # Perform OCR
            text = pytesseract.image_to_string(processed, lang=lang)
            
            # Clean up text
            text = text.strip()
            
            return text
        
        except Exception as e:
            logger.error(f"OCR text extraction failed: {e}")
            return ""
    
    def extract_number(
        self,
        image: np.ndarray,
        preprocess: bool = True
    ) -> Optional[int]:
        """
        Extract number from image
        
        Args:
            image: Input image
            preprocess: Whether to preprocess image
        
        Returns:
            Extracted number or None if extraction failed
        """
        if not self.available:
            logger.warning("OCR not available, returning None")
            return None
        
        try:
            # Preprocess if requested
            if preprocess:
                processed = self._preprocess_image(image)
            else:
                processed = image
            
            # Configure Tesseract for digits only
            config = '--psm 7 -c tessedit_char_whitelist=0123456789'
            text = pytesseract.image_to_string(processed, config=config)
            
            # Extract first number found
            numbers = re.findall(r'\d+', text)
            if numbers:
                return int(numbers[0])
            
            return None
        
        except Exception as e:
            logger.error(f"OCR number extraction failed: {e}")
            return None
    
    def extract_chinese_text(
        self,
        image: np.ndarray,
        preprocess: bool = True
    ) -> str:
        """
        Extract Chinese text from image
        
        Args:
            image: Input image
            preprocess: Whether to preprocess image
        
        Returns:
            Extracted Chinese text
        """
        return self.extract_text(image, lang='chi_sim', preprocess=preprocess)
    
    def _preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """
        Preprocess image to improve OCR accuracy
        
        Steps:
        1. Convert to grayscale
        2. Apply binary threshold
        3. Denoise
        
        Args:
            image: Input image
        
        Returns:
            Preprocessed image
        """
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        
        # Apply bilateral filter to reduce noise while keeping edges
        denoised = cv2.bilateralFilter(gray, 9, 75, 75)
        
        # Apply adaptive threshold
        binary = cv2.adaptiveThreshold(
            denoised,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            11,
            2
        )
        
        # Optional: morphological operations to clean up
        kernel = np.ones((2, 2), np.uint8)
        cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        
        return cleaned
    
    def is_available(self) -> bool:
        """Check if OCR service is available"""
        return self.available
    
    def get_tesseract_version(self) -> Optional[str]:
        """Get Tesseract version"""
        if not self.available:
            return None
        
        try:
            return pytesseract.get_tesseract_version()
        except Exception:
            return None
