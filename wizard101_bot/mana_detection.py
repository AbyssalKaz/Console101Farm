"""
Mana Detection System
Detects mana zero (exact) and mana low (approximate)
"""

import cv2
import numpy as np
from PIL import ImageGrab
import os
from typing import Optional, Tuple
from dataclasses import dataclass

@dataclass
class ManaStatus:
    """Current mana status"""
    is_zero: bool = False
    is_low: bool = False
    confidence: float = 0.0
    detected_region: Optional[Tuple[int, int, int, int]] = None

class ManaDetector:
    """
    Detects mana status using template matching.
    
    Methods:
    1. Exact zero detection - matches "0" template with high confidence
    2. Low mana detection - matches depleted orb appearance
    3. Digit detection - optional, for precise value reading
    """
    
    def __init__(self, images_folder: str = "images"):
        self.images_folder = images_folder
        
        # Templates
        self._zero_template = None
        self._empty_orb_template = None
        self._full_orb_template = None
        self._digit_templates = {}
        
        # Detection settings
        self.zero_confidence = 0.93
        self.low_confidence = 0.80
        self.low_threshold = 50
        
        # Region cache
        self.mana_region = None
    
    def load_templates(self) -> bool:
        """Load mana detection templates"""
        loaded = 0
        
        # Zero template (required)
        zero_path = os.path.join(self.images_folder, "mana_zero.png")
        if os.path.exists(zero_path):
            self._zero_template = cv2.imread(zero_path)
            if self._zero_template is not None:
                print("[+] Loaded mana_zero.png")
                loaded += 1
        else:
            print("[!] mana_zero.png not found")
        
        # Empty orb template (recommended)
        empty_path = os.path.join(self.images_folder, "mana_orb_empty.png")
        if os.path.exists(empty_path):
            self._empty_orb_template = cv2.imread(empty_path)
            if self._empty_orb_template is not None:
                print("[+] Loaded mana_orb_empty.png")
                loaded += 1
        
        # Full orb template (optional)
        full_path = os.path.join(self.images_folder, "mana_orb_full.png")
        if os.path.exists(full_path):
            self._full_orb_template = cv2.imread(full_path)
            if self._full_orb_template is not None:
                print("[+] Loaded mana_orb_full.png")
                loaded += 1
        
        # Load digit templates if available (0-9)
        for digit in range(10):
            digit_path = os.path.join(self.images_folder, f"mana_digit_{digit}.png")
            if os.path.exists(digit_path):
                template = cv2.imread(digit_path)
                if template is not None:
                    self._digit_templates[digit] = template
        
        if self._digit_templates:
            print(f"[+] Loaded {len(self._digit_templates)} digit templates")
        
        return loaded > 0
    
    def capture_screen(self) -> np.ndarray:
        """Capture current screen"""
        screenshot = ImageGrab.grab()
        return cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
    
    def find_template(self, screen: np.ndarray, template: np.ndarray, 
                      confidence: float = 0.8) -> Optional[Tuple[int, int, float]]:
        """Find template in screen, return (x, y, confidence) or None"""
        if template is None:
            return None
        
        try:
            result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            if max_val >= confidence:
                return (max_loc[0], max_loc[1], max_val)
        except Exception:
            pass
        
        return None
    
    def detect_zero(self, screen: Optional[np.ndarray] = None) -> Tuple[bool, float]:
        """
        Detect if mana is exactly zero using high-confidence matching.
        
        Returns: (is_zero, confidence)
        """
        if self._zero_template is None:
            return False, 0.0
        
        if screen is None:
            screen = self.capture_screen()
        
        result = self.find_template(screen, self._zero_template, self.zero_confidence)
        
        if result:
            x, y, conf = result
            h, w = self._zero_template.shape[:2]
            self.mana_region = (x, y, w, h)
            return True, conf
        
        return False, 0.0
    
    def detect_low_by_orb(self, screen: Optional[np.ndarray] = None) -> Tuple[bool, float]:
        """
        Detect low mana by matching the empty/depleted orb appearance.
        
        Returns: (is_low, confidence)
        """
        if self._empty_orb_template is None:
            return False, 0.0
        
        if screen is None:
            screen = self.capture_screen()
        
        result = self.find_template(screen, self._empty_orb_template, self.low_confidence)
        
        if result:
            return True, result[2]
        
        return False, 0.0
    
    def detect_low_digit(self, screen: np.ndarray) -> Tuple[bool, Optional[int]]:
        """
        Detect if a low digit (0-5) is showing, indicating low mana.
        
        Returns: (is_low_digit, detected_digit)
        """
        if not self._digit_templates:
            return False, None
        
        # Check for digits 0-5 (low mana indicators)
        for digit in range(6):
            if digit in self._digit_templates:
                result = self.find_template(screen, self._digit_templates[digit], 0.88)
                if result:
                    return True, digit
        
        return False, None
    
    def compare_orb_fullness(self, screen: np.ndarray) -> Optional[float]:
        """
        Compare current orb to full/empty templates.
        
        Returns: estimated fullness (0.0 = empty, 1.0 = full) or None
        """
        if self._full_orb_template is None or self._empty_orb_template is None:
            return None
        
        full_result = self.find_template(screen, self._full_orb_template, 0.6)
        empty_result = self.find_template(screen, self._empty_orb_template, 0.6)
        
        if full_result and empty_result:
            full_conf = full_result[2]
            empty_conf = empty_result[2]
            total = full_conf + empty_conf
            if total > 0:
                return full_conf / total
        elif full_result:
            return 0.8
        elif empty_result:
            return 0.2
        
        return None
    
    def check_status(self) -> ManaStatus:
        """
        Check current mana status.
        
        Returns ManaStatus with:
        - is_zero: True if mana is exactly 0
        - is_low: True if mana is low but not zero
        - confidence: Detection confidence
        """
        screen = self.capture_screen()
        status = ManaStatus()
        
        # Check for zero first (highest priority)
        is_zero, zero_conf = self.detect_zero(screen)
        if is_zero:
            status.is_zero = True
            status.is_low = True
            status.confidence = zero_conf
            status.detected_region = self.mana_region
            return status
        
        # Check for low mana by orb appearance
        is_low_orb, orb_conf = self.detect_low_by_orb(screen)
        if is_low_orb:
            status.is_low = True
            status.confidence = orb_conf
            return status
        
        # Check for low digits
        is_low_digit, digit = self.detect_low_digit(screen)
        if is_low_digit:
            status.is_low = True
            status.confidence = 0.85
            return status
        
        # Compare orb fullness as fallback
        fullness = self.compare_orb_fullness(screen)
        if fullness is not None and fullness < 0.3:
            status.is_low = True
            status.confidence = 0.7
        
        return status
    
    def is_mana_zero(self) -> bool:
        """Quick check if mana is zero"""
        is_zero, _ = self.detect_zero()
        return is_zero
    
    def is_mana_low(self) -> bool:
        """Quick check if mana is low"""
        status = self.check_status()
        return status.is_low

# Global instance
mana_detector = ManaDetector()