"""
Mana Refill Sequence Handler
Executes customizable combo sequences
"""

import time
from typing import Callable, Optional, List, Dict
from .config import config
from .controller_emulator import controller, XboxButton, BUTTON_MAP

class ComboExecutor:
    """Executes customizable combo sequences from config"""
    
    def __init__(self):
        self._running = False
        self._log_callback: Optional[Callable[[str], None]] = None
        self._last_action_time = time.time()
    
    def set_log_callback(self, callback: Callable[[str], None]):
        self._log_callback = callback
    
    def _log(self, message: str):
        if self._log_callback:
            self._log_callback(message)
        print(message)
    
    def update_action_time(self):
        self._last_action_time = time.time()
    
    def get_idle_time(self) -> float:
        return time.time() - self._last_action_time
    
    def should_refill(self, mana_is_zero: bool, mana_is_low: bool) -> bool:
        if not config.mana_refill.enabled:
            return False
        
        if mana_is_zero:
            return True
        
        if mana_is_low:
            idle_time = self.get_idle_time()
            if idle_time >= config.mana_refill.idle_timeout_seconds:
                self._log(f"[!] Low mana and idle for {idle_time:.0f}s, triggering refill")
                return True
        
        return False
    
    def _execute_step(self, step: Dict, stop_check: Optional[Callable[[], bool]] = None) -> bool:
        """Execute a single combo step"""
        action = step.get('action', '')
        value = step.get('value', '')
        duration = step.get('duration', 0.1)
        repeat = step.get('repeat', 1)
        
        for i in range(repeat):
            if stop_check and stop_check():
                return False
            
            if action == 'button':
                # Press a button
                if value.upper() in BUTTON_MAP:
                    self._log(f"    Button: {value}")
                    controller.press_button(BUTTON_MAP[value.upper()], duration)
                    time.sleep(0.1)
            
            elif action == 'wait':
                self._log(f"    Wait: {duration}s")
                time.sleep(duration)
            
            elif action == 'stick_forward':
                self._log(f"    Stick Forward: {duration}s")
                controller.set_stick(True, 0, 32767)
                controller.update()
                time.sleep(duration)
                controller.set_stick(True, 0, 0)
                controller.update()
            
            elif action == 'stick_back':
                self._log(f"    Stick Back: {duration}s")
                controller.set_stick(True, 0, -32768)
                controller.update()
                time.sleep(duration)
                controller.set_stick(True, 0, 0)
                controller.update()
            
            elif action == 'stick_left':
                self._log(f"    Stick Left: {duration}s")
                controller.set_stick(True, -32768, 0)
                controller.update()
                time.sleep(duration)
                controller.set_stick(True, 0, 0)
                controller.update()
            
            elif action == 'stick_right':
                self._log(f"    Stick Right: {duration}s")
                controller.set_stick(True, 32767, 0)
                controller.update()
                time.sleep(duration)
                controller.set_stick(True, 0, 0)
                controller.update()
            
            elif action == 'stick_hold':
                # Hold stick without releasing
                direction = value.lower()
                self._log(f"    Stick Hold: {direction}")
                if direction == 'left':
                    controller.set_stick(True, -32768, 0)
                elif direction == 'right':
                    controller.set_stick(True, 32767, 0)
                elif direction in ['up', 'forward']:
                    controller.set_stick(True, 0, 32767)
                elif direction in ['down', 'back']:
                    controller.set_stick(True, 0, -32768)
                controller.update()
                if duration > 0:
                    time.sleep(duration)
            
            elif action == 'stick_release':
                self._log(f"    Stick Release")
                controller.set_stick(True, 0, 0)
                controller.update()
            
            elif action == 'trigger_hold':
                is_left = value.lower() == 'left'
                self._log(f"    Trigger Hold: {'Left' if is_left else 'Right'}")
                controller.set_trigger(is_left, 255)
                controller.update()
                if duration > 0:
                    time.sleep(duration)
            
            elif action == 'trigger_release':
                is_left = value.lower() == 'left'
                self._log(f"    Trigger Release: {'Left' if is_left else 'Right'}")
                controller.set_trigger(is_left, 0)
                controller.update()
        
        return True
    
    def execute(self, stop_check: Callable[[], bool] = None) -> bool:
        """Execute the full combo sequence from config"""
        if self._running:
            return False
        
        self._running = True
        combo = config.mana_refill_combo
        
        try:
            self._log("[*] === STARTING COMBO SEQUENCE ===")
            self._log(f"[*] {len(combo)} steps to execute")
            
            for i, step in enumerate(combo):
                if stop_check and stop_check():
                    self._log("[X] Combo aborted")
                    return False
                
                self._log(f"[{i+1}/{len(combo)}] {step.get('action', 'unknown')}")
                
                if not self._execute_step(step, stop_check):
                    return False
            
            self._log("[*] === COMBO SEQUENCE COMPLETE ===")
            self.update_action_time()
            return True
            
        except Exception as e:
            self._log(f"[X] Combo error: {e}")
            return False
        finally:
            self._running = False
            controller.reset()
    
    @property
    def is_running(self) -> bool:
        return self._running

# Global instance
mana_refill = ComboExecutor()