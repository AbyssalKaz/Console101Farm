"""
Bot Engine - Core automation logic
Fixed enchant detection and casting
"""

import threading
import time
from typing import Optional, Callable, Tuple, List
from enum import Enum, auto

from .config import config
from .input_handler import input_handler
from .image_recognition import image_recognition, CardType, CardMatch
from .controller_emulator import controller
from .mana_detection import mana_detector, ManaStatus
from .mana_refill import mana_refill

class BotMode(Enum):
    SIMPLE = auto()
    ADVANCED = auto()

class BotState(Enum):
    STOPPED = auto()
    RUNNING = auto()
    PAUSED = auto()
    WAITING = auto()

class BotEngine:
    """Main bot automation engine"""
    
    def __init__(self):
        self.mode: BotMode = BotMode.SIMPLE
        self.state: BotState = BotState.STOPPED
        self.movement_enabled: bool = True
        
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._pause_event = threading.Event()
        self._pause_event.set()
        
        self._log_callback: Optional[Callable[[str], None]] = None
        self._state_callback: Optional[Callable[[BotState], None]] = None
        
        self.cycle_count: int = 0
        self.successful_casts: int = 0
        self._current_slot: int = 0
        
        # Debug mode
        self.debug_mode: bool = True
    
    def set_log_callback(self, callback: Callable[[str], None]):
        self._log_callback = callback
    
    def set_state_callback(self, callback: Callable[[BotState], None]):
        self._state_callback = callback
    
    def _log(self, message: str):
        timestamp = time.strftime("%H:%M:%S")
        full_message = f"[{timestamp}] {message}"
        print(full_message)
        if self._log_callback:
            self._log_callback(full_message)
    
    def _set_state(self, state: BotState):
        self.state = state
        if self._state_callback:
            self._state_callback(state)
    
    def _wait_while_paused(self):
        self._pause_event.wait()
    
    def _is_stopped(self) -> bool:
        return self._stop_event.is_set()
    
    def _check_mana(self) -> ManaStatus:
        status = mana_detector.check_status()
        
        if mana_refill.should_refill(status.is_zero, status.is_low):
            self._log("[!] Mana refill triggered")
            mana_refill.execute(stop_check=self._is_stopped)
        
        return status
    
    def _check_still_there(self) -> bool:
        if image_recognition.is_visible("still_there", config.images.confidence):
            self._log("[!] 'Still there?' prompt detected")
            self._handle_still_there()
            return True
        return False
    
    def _handle_still_there(self):
        was_enabled = controller.is_enabled
        
        if was_enabled:
            controller.disconnect()
            time.sleep(0.5)
        
        match = image_recognition.find_template("still_there", config.images.confidence)
        if match:
            cx, cy = match.center
            input_handler.mouse_click('left', cx, cy + 50)
            time.sleep(1)
        
        if was_enabled:
            time.sleep(0.5)
            controller.connect()
    
    def _press_key(self, key: str, hold_time: Optional[float] = None):
        self._wait_while_paused()
        if self._is_stopped():
            return
        
        if hold_time:
            input_handler.hold_key(key, hold_time)
        else:
            input_handler.press_key(key, config.timing.key_press_duration)
        
        time.sleep(config.timing.key_press_delay)
    
    def _select_card(self):
        """Press the card selection key"""
        self._log(f"    Pressing select: {config.bot_keys.select_card}")
        self._press_key(config.bot_keys.select_card)
    
    def _confirm_cast(self):
        """Press the confirm cast key"""
        self._log(f"    Pressing confirm: {config.bot_keys.confirm_cast}")
        self._press_key(config.bot_keys.confirm_cast)
    
    def _navigate_right(self, times: int = 1):
        """Navigate right in card hand"""
        for _ in range(times):
            self._press_key(config.bot_keys.navigate_right)
            time.sleep(0.15)
    
    def _navigate_left(self, times: int = 1):
        """Navigate left in card hand"""
        for _ in range(times):
            self._press_key(config.bot_keys.navigate_left)
            time.sleep(0.15)
    
    def _navigate_to_slot(self, target_slot: int):
        if target_slot == self._current_slot:
            return
        
        diff = target_slot - self._current_slot
        if diff > 0:
            self._log(f"    Navigating right {diff} times")
            self._navigate_right(diff)
        else:
            self._log(f"    Navigating left {abs(diff)} times")
            self._navigate_left(abs(diff))
        
        self._current_slot = target_slot
    
    def _find_all_cards(self) -> Tuple[List[CardMatch], List[CardMatch], List[CardMatch]]:
        """
        Find all cards and categorize them.
        Returns: (enchant_cards, spell_cards, enchanted_cards)
        """
        all_cards = image_recognition.find_cards(config.images.confidence)
        
        enchant_cards = []
        spell_cards = []
        enchanted_cards = []
        
        for card in all_cards:
            if card.card_type == CardType.ENCHANT:
                enchant_cards.append(card)
            elif card.card_type == CardType.SPELL:
                spell_cards.append(card)
            elif card.card_type == CardType.ENCHANTED_SPELL:
                enchanted_cards.append(card)
        
        if self.debug_mode:
            self._log(f"[DEBUG] Found {len(all_cards)} total cards:")
            self._log(f"    Enchants: {len(enchant_cards)}")
            self._log(f"    Spells: {len(spell_cards)}")
            self._log(f"    Enchanted: {len(enchanted_cards)}")
            for card in all_cards:
                self._log(f"    - {card.name} ({card.card_type.name}) x={card.x} conf={card.confidence:.2f}")
        
        return enchant_cards, spell_cards, enchanted_cards
    
    def _click_card_by_position(self, card: CardMatch):
        """Click directly on a card by its screen position"""
        cx, cy = card.center
        self._log(f"    Clicking card at ({cx}, {cy})")
        input_handler.mouse_click('left', cx, cy)
        time.sleep(0.3)
    
    def _wait_with_detection(self, seconds: float, message: str) -> Tuple[bool, bool]:
        self._log(f"{message} for {seconds}s...")
        
        elapsed = 0
        interval = config.timing.early_detect_interval
        
        while elapsed < seconds:
            if self._is_stopped():
                return False, False
            
            self._wait_while_paused()
            self._check_still_there()
            
            # Check for any cards
            enchant_cards, spell_cards, enchanted_cards = self._find_all_cards()
            if spell_cards or enchanted_cards:
                self._log(f"[!] Card detected early at {elapsed:.1f}s!")
                return True, True
            
            time.sleep(interval)
            elapsed += interval
        
        return True, False
    
    def _do_movement(self) -> bool:
        if not self.movement_enabled:
            return False
        
        self._log(f"[~] W/S movement ({config.movement.ws_repeats}x)")
        
        for i in range(config.movement.ws_repeats):
            if self._is_stopped():
                return False
            
            self._wait_while_paused()
            
            # Check for cards
            enchant_cards, spell_cards, enchanted_cards = self._find_all_cards()
            if spell_cards or enchanted_cards or enchant_cards:
                self._log("[!] Card detected during movement")
                return True
            
            input_handler.hold_key('w', config.movement.hold_duration)
            time.sleep(0.1)
            input_handler.hold_key('s', config.movement.hold_duration)
            time.sleep(0.2)
        
        return False
    
    def _run_simple_mode(self):
        """Simple mode: Just cast spell cards"""
        self._log("[*] Simple mode: Looking for spell cards...")
        
        while not self._is_stopped():
            self._wait_while_paused()
            self._check_mana()
            
            if self._check_still_there():
                continue
            
            enchant_cards, spell_cards, enchanted_cards = self._find_all_cards()
            
            # Cast enchanted first, then regular spells
            cards_to_cast = enchanted_cards + spell_cards
            
            if cards_to_cast:
                self._current_slot = 0
                card = cards_to_cast[0]
                
                self._log(f"[+] Casting {card.name}")
                
                # Click directly on the card
                self._click_card_by_position(card)
                time.sleep(0.3)
                
                # Confirm
                self._confirm_cast()
                
                self.successful_casts += 1
                mana_refill.update_action_time()
                
                completed, early = self._wait_with_detection(
                    config.timing.post_cast_wait,
                    "[*] Waiting for animation"
                )
                
                if not completed:
                    break
                
                if not early:
                    self._do_movement()
                
                continue
            
            time.sleep(config.timing.scan_interval)
    
    def _run_advanced_mode(self):
        """
        Advanced mode: Enchant + Cast
        
        Priority:
        1. If enchanted card exists -> cast it
        2. If enchant + spell exist -> enchant the spell
        3. If only spell exists -> cast it (no enchant available)
        """
        self._log("[*] Advanced mode: Looking for enchant + spell...")
        
        while not self._is_stopped():
            self._wait_while_paused()
            self._check_mana()
            
            if self._check_still_there():
                continue
            
            # Find all cards
            enchant_cards, spell_cards, enchanted_cards = self._find_all_cards()
            
            # ============================================
            # PRIORITY 1: Cast enchanted card if available
            # ============================================
            if enchanted_cards:
                card = enchanted_cards[0]
                self._log(f"[+] Found enchanted card: {card.name}")
                self._log(f"[+] Casting enchanted {card.name}!")
                
                # Click the enchanted card
                self._click_card_by_position(card)
                time.sleep(0.3)
                
                # Confirm cast
                self._confirm_cast()
                
                self.successful_casts += 1
                mana_refill.update_action_time()
                
                # Wait for battle animation
                completed, early = self._wait_with_detection(
                    config.timing.post_cast_wait,
                    "[*] Waiting for animation"
                )
                
                if not completed:
                    break
                
                if not early:
                    self._do_movement()
                
                continue
            
            # ============================================
            # PRIORITY 2: Enchant a spell if both available
            # ============================================
            if enchant_cards and spell_cards:
                enchant = enchant_cards[0]
                spell = spell_cards[0]
                
                self._log(f"[+] Found enchant: {enchant.name} (conf: {enchant.confidence:.2f})")
                self._log(f"[+] Found spell: {spell.name} (conf: {spell.confidence:.2f})")
                self._log(f"[+] Enchanting {spell.name} with {enchant.name}!")
                
                # Step 1: Click the enchant card (Colossal)
                self._log(f"    Step 1: Clicking enchant at ({enchant.center[0]}, {enchant.center[1]})")
                self._click_card_by_position(enchant)
                
                # Wait for enchant mode to activate
                time.sleep(0.8)
                
                # Step 2: Re-scan for the spell card (position may have changed)
                self._log("    Step 2: Re-scanning for spell card...")
                _, new_spell_cards, _ = self._find_all_cards()
                
                if new_spell_cards:
                    spell = new_spell_cards[0]
                    self._log(f"    Step 3: Clicking spell at ({spell.center[0]}, {spell.center[1]})")
                    self._click_card_by_position(spell)
                    time.sleep(0.5)
                    self._log("[+] Enchant applied! Waiting for next turn...")
                else:
                    self._log("[!] Lost spell card after enchant selection, retrying...")
                    # Press escape or B to cancel
                    self._press_key('escape')
                    time.sleep(0.5)
                
                # Small delay before next action
                time.sleep(1.0)
                continue
            
            # ============================================
            # PRIORITY 3: Cast unenchanted spell if no enchant
            # ============================================
            if spell_cards and not enchant_cards:
                card = spell_cards[0]
                self._log(f"[+] No enchant available, casting {card.name} directly")
                
                self._click_card_by_position(card)
                time.sleep(0.3)
                self._confirm_cast()
                
                self.successful_casts += 1
                mana_refill.update_action_time()
                
                completed, early = self._wait_with_detection(
                    config.timing.post_cast_wait,
                    "[*] Waiting for animation"
                )
                
                if not completed:
                    break
                
                if not early:
                    self._do_movement()
                
                continue
            
            # Nothing found, wait and scan again
            if self.debug_mode and not (enchant_cards or spell_cards or enchanted_cards):
                self._log("[*] No cards detected, waiting...")
            
            time.sleep(config.timing.scan_interval)
    
    def _run_loop(self):
        self._set_state(BotState.RUNNING)
        self.cycle_count = 0
        self._current_slot = 0
        
        # Load templates
        self._log("[*] Loading card templates...")
        
        # Load card templates with their types
        loaded = 0
        if image_recognition.load_card_template("tempest", config.images.tempest_image, CardType.SPELL):
            loaded += 1
        if image_recognition.load_card_template("colossal", config.images.colossal_image, CardType.ENCHANT):
            loaded += 1
        if image_recognition.load_card_template("tempest_enchanted", config.images.tempest_enchanted_image, CardType.ENCHANTED_SPELL):
            loaded += 1
        
        # Load UI templates
        image_recognition.load_template("still_there", config.images.still_there_prompt)
        mana_detector.load_templates()
        
        self._log(f"[*] Loaded {loaded} card templates")
        
        if loaded == 0:
            self._log("[!] WARNING: No card templates loaded! Check your images folder.")
        
        try:
            while not self._is_stopped():
                self.cycle_count += 1
                self._log(f"\n===== CYCLE {self.cycle_count} =====")
                
                if self.mode == BotMode.SIMPLE:
                    self._run_simple_mode()
                else:
                    self._run_advanced_mode()
                
        except Exception as e:
            self._log(f"[X] Error: {e}")
            import traceback
            traceback.print_exc()
        
        self._set_state(BotState.STOPPED)
        self._log("[*] Bot stopped")
    
    def start(self, mode: BotMode = BotMode.SIMPLE):
        if self.state == BotState.RUNNING:
            return
        
        self.mode = mode
        self._stop_event.clear()
        self._pause_event.set()
        
        self._log(f"[*] Starting bot in {mode.name} mode")
        
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
    
    def stop(self):
        self._log("[X] Stopping bot...")
        self._stop_event.set()
        self._pause_event.set()
        
        if self._thread:
            self._thread.join(timeout=2)
    
    def pause(self):
        self._pause_event.clear()
        self._set_state(BotState.PAUSED)
        self._log("[||] Paused")
    
    def resume(self):
        self._pause_event.set()
        self._set_state(BotState.RUNNING)
        self._log("[>] Resumed")
    
    def toggle_pause(self):
        if self.state == BotState.PAUSED:
            self.resume()
        elif self.state == BotState.RUNNING:
            self.pause()
    
    def toggle_movement(self):
        self.movement_enabled = not self.movement_enabled
        self._log(f"[*] Movement: {'Enabled' if self.movement_enabled else 'Disabled'}")

bot_engine = BotEngine()