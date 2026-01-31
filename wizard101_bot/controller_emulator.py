"""
Xbox Controller Emulation using ViGEmBus + vgamepad library
With rapid step movement for consistency
"""

import threading
import time
from typing import Optional, Dict, Callable
from enum import IntFlag

try:
    import vgamepad as vg
    VGAMEPAD_AVAILABLE = True
except ImportError:
    VGAMEPAD_AVAILABLE = False

class XboxButton(IntFlag):
    """Xbox controller button flags"""
    NONE = 0x0000
    DPAD_UP = 0x0001
    DPAD_DOWN = 0x0002
    DPAD_LEFT = 0x0004
    DPAD_RIGHT = 0x0008
    START = 0x0010
    BACK = 0x0020
    LEFT_THUMB = 0x0040
    RIGHT_THUMB = 0x0080
    LEFT_SHOULDER = 0x0100
    RIGHT_SHOULDER = 0x0200
    GUIDE = 0x0400
    A = 0x1000
    B = 0x2000
    X = 0x4000
    Y = 0x8000

BUTTON_MAP = {
    'A': XboxButton.A,
    'B': XboxButton.B,
    'X': XboxButton.X,
    'Y': XboxButton.Y,
    'DPAD_UP': XboxButton.DPAD_UP,
    'DPAD_DOWN': XboxButton.DPAD_DOWN,
    'DPAD_LEFT': XboxButton.DPAD_LEFT,
    'DPAD_RIGHT': XboxButton.DPAD_RIGHT,
    'LEFT_SHOULDER': XboxButton.LEFT_SHOULDER,
    'RIGHT_SHOULDER': XboxButton.RIGHT_SHOULDER,
    'LEFT_THUMB': XboxButton.LEFT_THUMB,
    'RIGHT_THUMB': XboxButton.RIGHT_THUMB,
    'START': XboxButton.START,
    'BACK': XboxButton.BACK,
    'GUIDE': XboxButton.GUIDE,
}

class ControllerState:
    def __init__(self):
        self.buttons: int = 0
        self.left_trigger: int = 0
        self.right_trigger: int = 0
        self.left_stick_x: int = 0
        self.left_stick_y: int = 0
        self.right_stick_x: int = 0
        self.right_stick_y: int = 0
    
    def reset(self):
        self.buttons = 0
        self.left_trigger = 0
        self.right_trigger = 0
        self.left_stick_x = 0
        self.left_stick_y = 0
        self.right_stick_x = 0
        self.right_stick_y = 0

class ControllerEmulator:
    """Virtual Xbox Controller with rapid step movement"""
    
    def __init__(self):
        self.state = ControllerState()
        self._gamepad = None
        self._enabled = False
        self._polling = False
        self._poll_thread: Optional[threading.Thread] = None
        self._log_callback: Optional[Callable] = None
        
        # Movement settings - rapid steps mode
        self.step_duration: float = 0.05  # How long each step lasts
        self.step_gap: float = 0.01       # Gap between steps
        self.use_rapid_steps: bool = True  # Enable rapid step mode
    
    def set_log_callback(self, callback: Callable):
        self._log_callback = callback
    
    def _log(self, msg: str):
        if self._log_callback:
            self._log_callback(msg)
    
    @property
    def is_available(self) -> bool:
        if not VGAMEPAD_AVAILABLE:
            return False
        try:
            test = vg.VX360Gamepad()
            del test
            return True
        except:
            return False
    
    @property
    def is_enabled(self) -> bool:
        return self._enabled
    
    def connect(self) -> bool:
        if not VGAMEPAD_AVAILABLE:
            print("[!] vgamepad not installed: pip install vgamepad")
            return False
        
        try:
            self._gamepad = vg.VX360Gamepad()
            self._enabled = True
            self.state.reset()
            self._apply_state()
            print("[+] Virtual Xbox controller connected!")
            return True
        except Exception as e:
            print(f"[!] Failed to connect: {e}")
            return False
    
    def disconnect(self):
        self.stop_polling()
        
        if self._gamepad:
            try:
                self._gamepad.reset()
                self._gamepad.update()
                del self._gamepad
            except:
                pass
            self._gamepad = None
        
        self._enabled = False
        print("[+] Controller disconnected")
    
    def _apply_state(self):
        if not self._enabled or not self._gamepad:
            return
        
        try:
            self._gamepad.reset()
            
            button_map = [
                (XboxButton.A, vg.XUSB_BUTTON.XUSB_GAMEPAD_A),
                (XboxButton.B, vg.XUSB_BUTTON.XUSB_GAMEPAD_B),
                (XboxButton.X, vg.XUSB_BUTTON.XUSB_GAMEPAD_X),
                (XboxButton.Y, vg.XUSB_BUTTON.XUSB_GAMEPAD_Y),
                (XboxButton.DPAD_UP, vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP),
                (XboxButton.DPAD_DOWN, vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN),
                (XboxButton.DPAD_LEFT, vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT),
                (XboxButton.DPAD_RIGHT, vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT),
                (XboxButton.START, vg.XUSB_BUTTON.XUSB_GAMEPAD_START),
                (XboxButton.BACK, vg.XUSB_BUTTON.XUSB_GAMEPAD_BACK),
                (XboxButton.LEFT_THUMB, vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_THUMB),
                (XboxButton.RIGHT_THUMB, vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_THUMB),
                (XboxButton.LEFT_SHOULDER, vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER),
                (XboxButton.RIGHT_SHOULDER, vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER),
                (XboxButton.GUIDE, vg.XUSB_BUTTON.XUSB_GAMEPAD_GUIDE),
            ]
            
            for our_btn, vg_btn in button_map:
                if self.state.buttons & our_btn:
                    self._gamepad.press_button(button=vg_btn)
            
            self._gamepad.left_trigger(value=self.state.left_trigger)
            self._gamepad.right_trigger(value=self.state.right_trigger)
            self._gamepad.left_joystick(x_value=self.state.left_stick_x, y_value=self.state.left_stick_y)
            self._gamepad.right_joystick(x_value=self.state.right_stick_x, y_value=self.state.right_stick_y)
            
            self._gamepad.update()
        except:
            pass
    
    def update(self):
        self._apply_state()
    
    def set_button(self, button: XboxButton, pressed: bool):
        if pressed:
            self.state.buttons |= button
        else:
            self.state.buttons &= ~button
        self.update()
    
    def set_button_by_name(self, name: str, pressed: bool):
        if name.upper() in BUTTON_MAP:
            self.set_button(BUTTON_MAP[name.upper()], pressed)
    
    def press_button(self, button: XboxButton, duration: float = 0.1):
        self.set_button(button, True)
        time.sleep(duration)
        self.set_button(button, False)
        time.sleep(0.05)
    
    def press_button_by_name(self, name: str, duration: float = 0.1):
        if name.upper() in BUTTON_MAP:
            self.press_button(BUTTON_MAP[name.upper()], duration)
    
    def set_trigger(self, left: bool, value: int):
        value = max(0, min(255, value))
        if left:
            self.state.left_trigger = value
        else:
            self.state.right_trigger = value
        self.update()
    
    def set_stick(self, left: bool, x: int, y: int):
        x = max(-32768, min(32767, x))
        y = max(-32768, min(32767, y))
        if left:
            self.state.left_stick_x = x
            self.state.left_stick_y = y
        else:
            self.state.right_stick_x = x
            self.state.right_stick_y = y
        self.update()
    
    def hold_stick_direction(self, direction: str, duration: float, left: bool = True):
        """Hold stick in a direction for duration"""
        directions = {
            'up': (0, 32767), 'down': (0, -32768),
            'left': (-32768, 0), 'right': (32767, 0),
            'forward': (0, 32767), 'back': (0, -32768),
        }
        
        if direction.lower() in directions:
            x, y = directions[direction.lower()]
            self.set_stick(left, x, y)
            time.sleep(duration)
            self.set_stick(left, 0, 0)
    
    def reset(self):
        self.state.reset()
        self.update()
    
    def start_polling(self, log_callback=None):
        if self._polling:
            return
        
        self._polling = True
        self._log_callback = log_callback
        self._poll_thread = threading.Thread(target=self._poll_loop_rapid_steps, daemon=True)
        self._poll_thread.start()
        print("[+] Controller polling started (rapid steps mode)")
    
    def stop_polling(self):
        self._polling = False
        if self._poll_thread:
            self._poll_thread.join(timeout=1)
            self._poll_thread = None
    
    def _poll_loop_rapid_steps(self):
        """
        Rapid steps polling - sends repeated short inputs for consistent movement
        This mimics tapping the stick rapidly rather than holding it
        """
        from .input_handler import input_handler
        from .config import config
        
        bindings = config.controller
        
        # Track when each direction was last sent
        last_step_time = {
            'up': 0, 'down': 0, 'left': 0, 'right': 0,
            'r_up': 0, 'r_down': 0, 'r_left': 0, 'r_right': 0,
        }
        
        step_interval = self.step_duration + self.step_gap  # Total time per step
        
        while self._polling and self._enabled:
            try:
                current_time = time.time()
                
                # === BUTTONS (always immediate) ===
                new_buttons = 0
                
                btn_map = [
                    (bindings.button_a, XboxButton.A),
                    (bindings.button_b, XboxButton.B),
                    (bindings.button_x, XboxButton.X),
                    (bindings.button_y, XboxButton.Y),
                    (bindings.left_bumper, XboxButton.LEFT_SHOULDER),
                    (bindings.right_bumper, XboxButton.RIGHT_SHOULDER),
                    (bindings.dpad_up, XboxButton.DPAD_UP),
                    (bindings.dpad_down, XboxButton.DPAD_DOWN),
                    (bindings.dpad_left, XboxButton.DPAD_LEFT),
                    (bindings.dpad_right, XboxButton.DPAD_RIGHT),
                    (bindings.left_stick_click, XboxButton.LEFT_THUMB),
                    (bindings.right_stick_click, XboxButton.RIGHT_THUMB),
                    (bindings.start, XboxButton.START),
                    (bindings.back, XboxButton.BACK),
                    (bindings.guide, XboxButton.GUIDE),
                ]
                
                for key, button in btn_map:
                    if key and input_handler.is_key_pressed(key):
                        new_buttons |= button
                
                # === TRIGGERS ===
                left_trigger, right_trigger = 0, 0
                
                if bindings.left_trigger and input_handler.is_key_pressed(bindings.left_trigger):
                    left_trigger = 255
                if bindings.right_trigger and input_handler.is_key_pressed(bindings.right_trigger):
                    right_trigger = 255
                
                # Mouse triggers
                import ctypes
                user32 = ctypes.windll.user32
                
                if bindings.mouse_left_trigger:
                    if user32.GetAsyncKeyState(0x01) & 0x8000:
                        if bindings.mouse_left_is_right_trigger:
                            right_trigger = 255
                        else:
                            left_trigger = 255
                
                if bindings.mouse_right_trigger:
                    if user32.GetAsyncKeyState(0x02) & 0x8000:
                        if bindings.mouse_left_is_right_trigger:
                            left_trigger = 255
                        else:
                            right_trigger = 255
                
                # === LEFT STICK - RAPID STEPS ===
                left_x, left_y = 0, 0
                
                # Check each direction and send rapid steps
                if bindings.left_stick_up and input_handler.is_key_pressed(bindings.left_stick_up):
                    if current_time - last_step_time['up'] >= step_interval:
                        left_y = 32767
                        last_step_time['up'] = current_time
                    elif current_time - last_step_time['up'] < self.step_duration:
                        left_y = 32767  # Still in step duration
                
                if bindings.left_stick_down and input_handler.is_key_pressed(bindings.left_stick_down):
                    if current_time - last_step_time['down'] >= step_interval:
                        left_y = -32768
                        last_step_time['down'] = current_time
                    elif current_time - last_step_time['down'] < self.step_duration:
                        left_y = -32768
                
                if bindings.left_stick_left and input_handler.is_key_pressed(bindings.left_stick_left):
                    if current_time - last_step_time['left'] >= step_interval:
                        left_x = -32768
                        last_step_time['left'] = current_time
                    elif current_time - last_step_time['left'] < self.step_duration:
                        left_x = -32768
                
                if bindings.left_stick_right and input_handler.is_key_pressed(bindings.left_stick_right):
                    if current_time - last_step_time['right'] >= step_interval:
                        left_x = 32767
                        last_step_time['right'] = current_time
                    elif current_time - last_step_time['right'] < self.step_duration:
                        left_x = 32767
                
                # === RIGHT STICK - RAPID STEPS ===
                right_x, right_y = 0, 0
                
                if bindings.right_stick_up and input_handler.is_key_pressed(bindings.right_stick_up):
                    if current_time - last_step_time['r_up'] >= step_interval:
                        right_y = 32767
                        last_step_time['r_up'] = current_time
                    elif current_time - last_step_time['r_up'] < self.step_duration:
                        right_y = 32767
                
                if bindings.right_stick_down and input_handler.is_key_pressed(bindings.right_stick_down):
                    if current_time - last_step_time['r_down'] >= step_interval:
                        right_y = -32768
                        last_step_time['r_down'] = current_time
                    elif current_time - last_step_time['r_down'] < self.step_duration:
                        right_y = -32768
                
                if bindings.right_stick_left and input_handler.is_key_pressed(bindings.right_stick_left):
                    if current_time - last_step_time['r_left'] >= step_interval:
                        right_x = -32768
                        last_step_time['r_left'] = current_time
                    elif current_time - last_step_time['r_left'] < self.step_duration:
                        right_x = -32768
                
                if bindings.right_stick_right and input_handler.is_key_pressed(bindings.right_stick_right):
                    if current_time - last_step_time['r_right'] >= step_interval:
                        right_x = 32767
                        last_step_time['r_right'] = current_time
                    elif current_time - last_step_time['r_right'] < self.step_duration:
                        right_x = 32767
                
                # === APPLY STATE ===
                self.state.buttons = new_buttons
                self.state.left_stick_x = left_x
                self.state.left_stick_y = left_y
                self.state.right_stick_x = right_x
                self.state.right_stick_y = right_y
                self.state.left_trigger = left_trigger
                self.state.right_trigger = right_trigger
                
                self.update()
                
                # Fast poll rate
                time.sleep(0.005)
                
            except Exception as e:
                time.sleep(0.01)

controller = ControllerEmulator()