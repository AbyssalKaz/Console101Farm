"""
Configuration management for the Wizard101 Bot Suite
"""

import json
import os
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple

CONFIG_FILE = "config.json"

@dataclass
class TimingConfig:
    """Timing settings"""
    key_press_duration: float = 0.08
    key_press_delay: float = 0.25
    action_delay: float = 1.5
    hold_duration: float = 1.0
    post_cast_wait: float = 20.0
    scan_interval: float = 0.5
    early_detect_interval: float = 0.25

@dataclass
class MovementConfig:
    """Movement settings"""
    enabled: bool = True
    ws_repeats: int = 3
    hold_duration: float = 1.0

@dataclass
class ComboStep:
    """Single step in a combo sequence"""
    action: str  # button, stick, trigger, wait
    value: str   # Button name, direction, or wait time
    duration: float = 0.1  # How long to hold/wait
    repeat: int = 1  # How many times to repeat

@dataclass 
class ManaRefillConfig:
    """Mana refill sequence settings"""
    enabled: bool = True
    low_mana_threshold: int = 50
    idle_timeout_seconds: float = 180.0
    
    # Movement timings
    initial_forward_hold: float = 2.0
    second_forward_hold: float = 2.0
    third_forward_hold: float = 2.0
    turn_right_hold: float = 1.0
    final_forward_hold: float = 2.0
    
    # Wait timings
    wait_after_potion_select: float = 7.0
    wait_after_use: float = 5.0
    wait_between_movements: float = 2.0

@dataclass
class ImageConfig:
    """Image recognition settings"""
    folder: str = "images"
    confidence: float = 0.8
    high_confidence: float = 0.95
    
    # Card images
    tempest_image: str = "tempest.png"
    colossal_image: str = "colossal.png"
    tempest_enchanted_image: str = "tempest_enchanted.png"
    
    # UI images
    still_there_prompt: str = "still_there.png"
    
    # Mana detection
    mana_zero: str = "mana_zero.png"
    mana_low: str = "mana_low.png"
    mana_orb_empty: str = "mana_orb_empty.png"
    mana_orb_full: str = "mana_orb_full.png"

@dataclass
class ControllerBindings:
    """All controller button bindings"""
    # Face buttons
    button_a: str = "space"
    button_b: str = "lctrl"
    button_x: str = "r"
    button_y: str = "1"
    
    # Bumpers
    left_bumper: str = "e"
    right_bumper: str = "q"
    
    # Triggers
    left_trigger: str = ""
    right_trigger: str = ""
    
    # D-Pad
    dpad_up: str = "up"
    dpad_down: str = "down"
    dpad_left: str = "left"
    dpad_right: str = "right"
    
    # Stick clicks
    left_stick_click: str = "lshift"
    right_stick_click: str = "c"
    
    # Menu buttons
    start: str = "b"
    back: str = "v"
    guide: str = "tilde"
    
    # Left stick movement
    left_stick_up: str = "w"
    left_stick_down: str = "s"
    left_stick_left: str = "a"
    left_stick_right: str = "d"
    
    # Right stick movement
    right_stick_up: str = ""
    right_stick_down: str = ""
    right_stick_left: str = ""
    right_stick_right: str = ""
    
    # Mouse bindings
    mouse_left_trigger: bool = True
    mouse_right_trigger: bool = True
    mouse_left_is_right_trigger: bool = True

@dataclass
class BotKeysConfig:
    """Keys the bot uses for actions"""
    select_card: str = "space"  # Key to select/confirm cards (A button)
    confirm_cast: str = "space"  # Key to confirm casting
    navigate_left: str = "left"
    navigate_right: str = "right"

@dataclass
class HotkeyConfig:
    """Application hotkeys"""
    stop: str = "numpad1"
    pause: str = "u"
    toggle_movement: str = "i"
    toggle_controller: str = "f1"

@dataclass
class WindowConfig:
    """Window settings"""
    width: int = 900
    height: int = 700
    min_width: int = 600
    min_height: int = 400

@dataclass
class AppConfig:
    """Main application configuration"""
    timing: TimingConfig = field(default_factory=TimingConfig)
    movement: MovementConfig = field(default_factory=MovementConfig)
    mana_refill: ManaRefillConfig = field(default_factory=ManaRefillConfig)
    images: ImageConfig = field(default_factory=ImageConfig)
    controller: ControllerBindings = field(default_factory=ControllerBindings)
    bot_keys: BotKeysConfig = field(default_factory=BotKeysConfig)
    hotkeys: HotkeyConfig = field(default_factory=HotkeyConfig)
    window: WindowConfig = field(default_factory=WindowConfig)
    
    # Bot mode
    mode: str = "simple"
    use_coordinate_detection: bool = False
    
    # Custom combo sequence (editable)
    mana_refill_combo: List[dict] = field(default_factory=lambda: [
        {"action": "button", "value": "RIGHT_SHOULDER", "duration": 0.1, "repeat": 1},
        {"action": "stick_hold", "value": "left", "duration": 0.2, "repeat": 1},
        {"action": "button", "value": "RIGHT_SHOULDER", "duration": 0.1, "repeat": 1},
        {"action": "stick_release", "value": "left", "duration": 0.0, "repeat": 1},
        {"action": "wait", "value": "", "duration": 7.0, "repeat": 1},
        {"action": "button", "value": "LEFT_SHOULDER", "duration": 0.1, "repeat": 4},
        {"action": "button", "value": "A", "duration": 0.1, "repeat": 1},
        {"action": "button", "value": "DPAD_DOWN", "duration": 0.1, "repeat": 4},
        {"action": "button", "value": "A", "duration": 0.1, "repeat": 1},
        {"action": "wait", "value": "", "duration": 5.0, "repeat": 1},
        {"action": "stick_forward", "value": "", "duration": 2.0, "repeat": 1},
        {"action": "wait", "value": "", "duration": 5.0, "repeat": 1},
        {"action": "stick_forward", "value": "", "duration": 2.0, "repeat": 1},
        {"action": "wait", "value": "", "duration": 5.0, "repeat": 1},
        {"action": "stick_forward", "value": "", "duration": 2.0, "repeat": 1},
        {"action": "wait", "value": "", "duration": 2.0, "repeat": 1},
        {"action": "stick_right", "value": "", "duration": 1.0, "repeat": 1},
        {"action": "stick_forward", "value": "", "duration": 2.0, "repeat": 1},
        {"action": "wait", "value": "", "duration": 2.0, "repeat": 1},
        {"action": "button", "value": "X", "duration": 0.1, "repeat": 1},
        {"action": "button", "value": "DPAD_DOWN", "duration": 0.1, "repeat": 1},
        {"action": "button", "value": "X", "duration": 0.1, "repeat": 1},
        {"action": "wait", "value": "", "duration": 2.0, "repeat": 1},
        {"action": "button", "value": "B", "duration": 0.1, "repeat": 1},
        {"action": "trigger_hold", "value": "right", "duration": 0.0, "repeat": 1},
        {"action": "stick_hold", "value": "left", "duration": 1.0, "repeat": 1},
        {"action": "trigger_release", "value": "right", "duration": 0.0, "repeat": 1},
        {"action": "stick_release", "value": "left", "duration": 0.0, "repeat": 1},
        {"action": "button", "value": "DPAD_LEFT", "duration": 0.1, "repeat": 1},
        {"action": "stick_forward", "value": "", "duration": 2.0, "repeat": 1},
    ])
    
    def save(self, filepath: str = CONFIG_FILE):
        """Save configuration to JSON file"""
        with open(filepath, 'w') as f:
            json.dump(asdict(self), f, indent=2)
    
    @classmethod
    def load(cls, filepath: str = CONFIG_FILE) -> 'AppConfig':
        """Load configuration from JSON file"""
        if not os.path.exists(filepath):
            config = cls()
            config.save(filepath)
            return config
        
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            return cls(
                timing=TimingConfig(**data.get('timing', {})),
                movement=MovementConfig(**data.get('movement', {})),
                mana_refill=ManaRefillConfig(**data.get('mana_refill', {})),
                images=ImageConfig(**data.get('images', {})),
                controller=ControllerBindings(**data.get('controller', {})),
                bot_keys=BotKeysConfig(**data.get('bot_keys', {})),
                hotkeys=HotkeyConfig(**data.get('hotkeys', {})),
                window=WindowConfig(**data.get('window', {})),
                mode=data.get('mode', 'simple'),
                use_coordinate_detection=data.get('use_coordinate_detection', False),
                mana_refill_combo=data.get('mana_refill_combo', cls().mana_refill_combo)
            )
        except Exception as e:
            print(f"[!] Error loading config: {e}, using defaults")
            return cls()

# Global config instance
config = AppConfig.load()