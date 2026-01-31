"""
Image Recognition Module
Handles screen capture and template matching for card detection
Supports image-only card detection without coordinates
"""

import cv2
import numpy as np
from PIL import ImageGrab
import os
from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass
from enum import Enum, auto

class CardType(Enum):
    """Types of cards we can detect"""
    SPELL = auto()
    ENCHANT = auto()
    ENCHANTED_SPELL = auto()
    UNKNOWN = auto()

@dataclass
class CardMatch:
    """Represents a detected card"""
    x: int
    y: int
    width: int
    height: int
    confidence: float
    card_type: CardType
    name: str
    
    @property
    def center(self) -> Tuple[int, int]:
        return (self.x + self.width // 2, self.y + self.height // 2)

@dataclass
class Match:
    """Represents a detected image match"""
    x: int
    y: int
    width: int
    height: int
    confidence: float
    
    @property
    def center(self) -> Tuple[int, int]:
        return (self.x + self.width // 2, self.y + self.height // 2)

class ImageRecognition:
    """Handles image detection on screen"""
    
    def __init__(self, images_folder: str = "images"):
        self.images_folder = images_folder
        self._templates: Dict[str, np.ndarray] = {}
        self._card_templates: Dict[str, Tuple[np.ndarray, CardType]] = {}
        
        if not os.path.exists(images_folder):
            os.makedirs(images_folder)
    
    def load_template(self, name: str, filename: str) -> bool:
        """Load a template image"""
        path = os.path.join(self.images_folder, filename)
        if not os.path.exists(path):
            print(f"[!] Template not found: {path}")
            return False
        
        template = cv2.imread(path)
        if template is None:
            print(f"[!] Could not load template: {path}")
            return False
        
        self._templates[name] = template
        print(f"[+] Loaded template: {name}")
        return True
    
    def load_card_template(self, name: str, filename: str, card_type: CardType) -> bool:
        """Load a card template with type information"""
        path = os.path.join(self.images_folder, filename)
        if not os.path.exists(path):
            print(f"[!] Card template not found: {path}")
            return False
        
        template = cv2.imread(path)
        if template is None:
            print(f"[!] Could not load card template: {path}")
            return False
        
        self._card_templates[name] = (template, card_type)
        print(f"[+] Loaded card template: {name} ({card_type.name})")
        return True
    
    def capture_screen(self) -> np.ndarray:
        """Capture the current screen"""
        screenshot = ImageGrab.grab()
        screenshot_np = np.array(screenshot)
        return cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)
    
    def find_template(self, name: str, confidence: float = 0.8) -> Optional[Match]:
        """Find a single instance of a template on screen"""
        if name not in self._templates:
            return None
        
        template = self._templates[name]
        screen = self.capture_screen()
        
        try:
            result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            if max_val >= confidence:
                h, w = template.shape[:2]
                return Match(
                    x=max_loc[0],
                    y=max_loc[1],
                    width=w,
                    height=h,
                    confidence=max_val
                )
        except Exception:
            pass
        
        return None
    
    def find_all_templates(self, name: str, confidence: float = 0.8) -> List[Match]:
        """Find all instances of a template on screen"""
        if name not in self._templates:
            return []
        
        template = self._templates[name]
        screen = self.capture_screen()
        
        try:
            result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
            locations = np.where(result >= confidence)
            
            h, w = template.shape[:2]
            matches = []
            
            for pt in zip(*locations[::-1]):
                x, y = pt
                
                # Check for duplicates
                is_duplicate = False
                for existing in matches:
                    if abs(x - existing.x) < w * 0.5 and abs(y - existing.y) < h * 0.5:
                        is_duplicate = True
                        break
                
                if not is_duplicate:
                    matches.append(Match(
                        x=x, y=y, width=w, height=h,
                        confidence=result[y, x]
                    ))
            
            matches.sort(key=lambda m: m.x)
            return matches
        except Exception:
            return []
    
    def find_cards(self, confidence: float = 0.8) -> List[CardMatch]:
        """
        Find all cards on screen using image templates only.
        Returns cards sorted by x position (left to right).
        """
        screen = self.capture_screen()
        all_cards: List[CardMatch] = []
        
        for name, (template, card_type) in self._card_templates.items():
            try:
                result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
                locations = np.where(result >= confidence)
                
                h, w = template.shape[:2]
                
                for pt in zip(*locations[::-1]):
                    x, y = pt
                    
                    # Check for duplicates
                    is_duplicate = False
                    for existing in all_cards:
                        if abs(x - existing.x) < w * 0.5 and abs(y - existing.y) < h * 0.5:
                            if result[y, x] > existing.confidence:
                                all_cards.remove(existing)
                            else:
                                is_duplicate = True
                            break
                    
                    if not is_duplicate:
                        all_cards.append(CardMatch(
                            x=x, y=y, width=w, height=h,
                            confidence=result[y, x],
                            card_type=card_type,
                            name=name
                        ))
            except Exception:
                continue
        
        all_cards.sort(key=lambda c: c.x)
        return all_cards
    
    def find_card_by_type(self, card_type: CardType, confidence: float = 0.8) -> List[CardMatch]:
        """Find all cards of a specific type"""
        all_cards = self.find_cards(confidence)
        return [c for c in all_cards if c.card_type == card_type]
    
    def find_enchant_cards(self, confidence: float = 0.8) -> List[CardMatch]:
        """Find all enchant cards"""
        return self.find_card_by_type(CardType.ENCHANT, confidence)
    
    def find_spell_cards(self, confidence: float = 0.8) -> List[CardMatch]:
        """Find all spell cards (unenchanted)"""
        return self.find_card_by_type(CardType.SPELL, confidence)
    
    def find_enchanted_cards(self, confidence: float = 0.8) -> List[CardMatch]:
        """Find all enchanted spell cards"""
        return self.find_card_by_type(CardType.ENCHANTED_SPELL, confidence)
    
    def get_card_slot_index(self, card: CardMatch, all_cards: List[CardMatch]) -> int:
        """Get the slot index of a card (0-indexed, left to right)"""
        sorted_cards = sorted(all_cards, key=lambda c: c.x)
        for i, c in enumerate(sorted_cards):
            if c.x == card.x and c.y == card.y:
                return i
        return 0
    
    def get_navigation_keys(self, from_slot: int, to_slot: int) -> List[str]:
        """Get key presses needed to navigate between slots"""
        diff = to_slot - from_slot
        if diff > 0:
            return ['right'] * diff
        elif diff < 0:
            return ['left'] * abs(diff)
        return []
    
    def is_visible(self, name: str, confidence: float = 0.8) -> bool:
        """Check if a template is visible on screen"""
        return self.find_template(name, confidence) is not None

# Global instance
image_recognition = ImageRecognition()