"""
Hardware-level input handling using Windows SendInput API
Supports both keyboard simulation and controller emulation
"""

import ctypes
from ctypes import wintypes, Structure, Union, POINTER, sizeof
import time
import threading
from typing import Optional, Callable, Dict
from enum import IntEnum, IntFlag

# ============== WINDOWS API SETUP ==============

user32 = ctypes.WinDLL('user32', use_last_error=True)

# Input type constants
INPUT_MOUSE = 0
INPUT_KEYBOARD = 1
INPUT_HARDWARE = 2

# Key event flags
KEYEVENTF_EXTENDEDKEY = 0x0001
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_UNICODE = 0x0004
KEYEVENTF_SCANCODE = 0x0008

# Mouse event flags
MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
MOUSEEVENTF_ABSOLUTE = 0x8000

# ============== SCAN CODES ==============

class ScanCode(IntEnum):
    """DirectInput Scan Codes"""
    # Letters
    A = 0x1E
    B = 0x30
    C = 0x2E
    D = 0x20
    E = 0x12
    F = 0x21
    G = 0x22
    H = 0x23
    I = 0x17
    J = 0x24
    K = 0x25
    L = 0x26
    M = 0x32
    N = 0x31
    O = 0x18
    P = 0x19
    Q = 0x10
    R = 0x13
    S = 0x1F
    T = 0x14
    U = 0x16
    V = 0x2F
    W = 0x11
    X = 0x2D
    Y = 0x15
    Z = 0x2C
    
    # Numbers
    N0 = 0x0B
    N1 = 0x02
    N2 = 0x03
    N3 = 0x04
    N4 = 0x05
    N5 = 0x06
    N6 = 0x07
    N7 = 0x08
    N8 = 0x09
    N9 = 0x0A
    
    # Function keys
    F1 = 0x3B
    F2 = 0x3C
    F3 = 0x3D
    F4 = 0x3E
    F5 = 0x3F
    F6 = 0x40
    F7 = 0x41
    F8 = 0x42
    F9 = 0x43
    F10 = 0x44
    F11 = 0x57
    F12 = 0x58
    
    # Special keys
    ESCAPE = 0x01
    ENTER = 0x1C
    SPACE = 0x39
    BACKSPACE = 0x0E
    TAB = 0x0F
    LSHIFT = 0x2A
    RSHIFT = 0x36
    LCTRL = 0x1D
    RCTRL = 0x1D  # Extended
    LALT = 0x38
    RALT = 0x38   # Extended
    CAPSLOCK = 0x3A
    TILDE = 0x29
    
    # Arrow keys (Extended)
    UP = 0x48
    DOWN = 0x50
    LEFT = 0x4B
    RIGHT = 0x4D
    
    # Numpad
    NUMPAD0 = 0x52
    NUMPAD1 = 0x4F
    NUMPAD2 = 0x50
    NUMPAD3 = 0x51
    NUMPAD4 = 0x4B
    NUMPAD5 = 0x4C
    NUMPAD6 = 0x4D
    NUMPAD7 = 0x47
    NUMPAD8 = 0x48
    NUMPAD9 = 0x49

# Extended keys that need special flag
EXTENDED_KEYS = {
    ScanCode.UP, ScanCode.DOWN, ScanCode.LEFT, ScanCode.RIGHT,
    ScanCode.RCTRL, ScanCode.RALT
}

# String to scan code mapping
KEY_MAP: Dict[str, ScanCode] = {
    # Letters (lowercase)
    'a': ScanCode.A, 'b': ScanCode.B, 'c': ScanCode.C, 'd': ScanCode.D,
    'e': ScanCode.E, 'f': ScanCode.F, 'g': ScanCode.G, 'h': ScanCode.H,
    'i': ScanCode.I, 'j': ScanCode.J, 'k': ScanCode.K, 'l': ScanCode.L,
    'm': ScanCode.M, 'n': ScanCode.N, 'o': ScanCode.O, 'p': ScanCode.P,
    'q': ScanCode.Q, 'r': ScanCode.R, 's': ScanCode.S, 't': ScanCode.T,
    'u': ScanCode.U, 'v': ScanCode.V, 'w': ScanCode.W, 'x': ScanCode.X,
    'y': ScanCode.Y, 'z': ScanCode.Z,
    
    # Numbers
    '0': ScanCode.N0, '1': ScanCode.N1, '2': ScanCode.N2, '3': ScanCode.N3,
    '4': ScanCode.N4, '5': ScanCode.N5, '6': ScanCode.N6, '7': ScanCode.N7,
    '8': ScanCode.N8, '9': ScanCode.N9,
    
    # Special keys
    'enter': ScanCode.ENTER, 'return': ScanCode.ENTER,
    'space': ScanCode.SPACE, 'escape': ScanCode.ESCAPE, 'esc': ScanCode.ESCAPE,
    'tab': ScanCode.TAB, 'backspace': ScanCode.BACKSPACE,
    'lshift': ScanCode.LSHIFT, 'rshift': ScanCode.RSHIFT, 'shift': ScanCode.LSHIFT,
    'lctrl': ScanCode.LCTRL, 'rctrl': ScanCode.RCTRL, 'ctrl': ScanCode.LCTRL,
    'lalt': ScanCode.LALT, 'ralt': ScanCode.RALT, 'alt': ScanCode.LALT,
    'tilde': ScanCode.TILDE, '`': ScanCode.TILDE,
    
    # Arrows
    'up': ScanCode.UP, 'down': ScanCode.DOWN,
    'left': ScanCode.LEFT, 'right': ScanCode.RIGHT,
    
    # Function keys
    'f1': ScanCode.F1, 'f2': ScanCode.F2, 'f3': ScanCode.F3, 'f4': ScanCode.F4,
    'f5': ScanCode.F5, 'f6': ScanCode.F6, 'f7': ScanCode.F7, 'f8': ScanCode.F8,
    'f9': ScanCode.F9, 'f10': ScanCode.F10, 'f11': ScanCode.F11, 'f12': ScanCode.F12,
    
    # Numpad
    'numpad0': ScanCode.NUMPAD0, 'numpad1': ScanCode.NUMPAD1,
    'numpad2': ScanCode.NUMPAD2, 'numpad3': ScanCode.NUMPAD3,
    'numpad4': ScanCode.NUMPAD4, 'numpad5': ScanCode.NUMPAD5,
    'numpad6': ScanCode.NUMPAD6, 'numpad7': ScanCode.NUMPAD7,
    'numpad8': ScanCode.NUMPAD8, 'numpad9': ScanCode.NUMPAD9,
}

# Virtual key codes (for GetAsyncKeyState)
VK_CODES = {
    'numpad0': 0x60, 'numpad1': 0x61, 'numpad2': 0x62, 'numpad3': 0x63,
    'numpad4': 0x64, 'numpad5': 0x65, 'numpad6': 0x66, 'numpad7': 0x67,
    'numpad8': 0x68, 'numpad9': 0x69,
    'f1': 0x70, 'f2': 0x71, 'f3': 0x72, 'f4': 0x73,
    'f5': 0x74, 'f6': 0x75, 'f7': 0x76, 'f8': 0x77,
    'f9': 0x78, 'f10': 0x79, 'f11': 0x7A, 'f12': 0x7B,
    'a': 0x41, 'b': 0x42, 'c': 0x43, 'd': 0x44, 'e': 0x45,
    'f': 0x46, 'g': 0x47, 'h': 0x48, 'i': 0x49, 'j': 0x4A,
    'k': 0x4B, 'l': 0x4C, 'm': 0x4D, 'n': 0x4E, 'o': 0x4F,
    'p': 0x50, 'q': 0x51, 'r': 0x52, 's': 0x53, 't': 0x54,
    'u': 0x55, 'v': 0x56, 'w': 0x57, 'x': 0x58, 'y': 0x59, 'z': 0x5A,
    'space': 0x20, 'enter': 0x0D, 'escape': 0x1B, 'tab': 0x09,
    'up': 0x26, 'down': 0x28, 'left': 0x25, 'right': 0x27,
    'lshift': 0xA0, 'rshift': 0xA1, 'lctrl': 0xA2, 'rctrl': 0xA3,
}

# ============== INPUT STRUCTURES ==============

class MOUSEINPUT(Structure):
    _fields_ = [
        ('dx', ctypes.c_long),
        ('dy', ctypes.c_long),
        ('mouseData', wintypes.DWORD),
        ('dwFlags', wintypes.DWORD),
        ('time', wintypes.DWORD),
        ('dwExtraInfo', POINTER(ctypes.c_ulong))
    ]

class KEYBDINPUT(Structure):
    _fields_ = [
        ('wVk', wintypes.WORD),
        ('wScan', wintypes.WORD),
        ('dwFlags', wintypes.DWORD),
        ('time', wintypes.DWORD),
        ('dwExtraInfo', POINTER(ctypes.c_ulong))
    ]

class HARDWAREINPUT(Structure):
    _fields_ = [
        ('uMsg', wintypes.DWORD),
        ('wParamL', wintypes.WORD),
        ('wParamH', wintypes.WORD)
    ]

class _INPUTunion(Union):
    _fields_ = [
        ('mi', MOUSEINPUT),
        ('ki', KEYBDINPUT),
        ('hi', HARDWAREINPUT)
    ]

class INPUT(Structure):
    _fields_ = [
        ('type', wintypes.DWORD),
        ('union', _INPUTunion)
    ]

# ============== INPUT HANDLER CLASS ==============

class InputHandler:
    """Handles all keyboard and mouse input at hardware level"""
    
    def __init__(self):
        self._extra = ctypes.pointer(ctypes.c_ulong(0))
    
    def _send_input(self, *inputs):
        """Send multiple input events"""
        n = len(inputs)
        arr = (INPUT * n)(*inputs)
        return user32.SendInput(n, arr, sizeof(INPUT))
    
    def _create_key_input(self, scan_code: int, flags: int) -> INPUT:
        """Create keyboard input structure"""
        inp = INPUT()
        inp.type = INPUT_KEYBOARD
        inp.union.ki.wVk = 0
        inp.union.ki.wScan = scan_code
        inp.union.ki.dwFlags = flags
        inp.union.ki.time = 0
        inp.union.ki.dwExtraInfo = self._extra
        return inp
    
    def key_down(self, key: str):
        """Press a key down"""
        key_lower = key.lower()
        if key_lower not in KEY_MAP:
            return False
        
        scan_code = KEY_MAP[key_lower]
        flags = KEYEVENTF_SCANCODE
        if scan_code in EXTENDED_KEYS or key_lower in ['up', 'down', 'left', 'right']:
            flags |= KEYEVENTF_EXTENDEDKEY
        
        inp = self._create_key_input(scan_code, flags)
        self._send_input(inp)
        return True
    
    def key_up(self, key: str):
        """Release a key"""
        key_lower = key.lower()
        if key_lower not in KEY_MAP:
            return False
        
        scan_code = KEY_MAP[key_lower]
        flags = KEYEVENTF_SCANCODE | KEYEVENTF_KEYUP
        if scan_code in EXTENDED_KEYS or key_lower in ['up', 'down', 'left', 'right']:
            flags |= KEYEVENTF_EXTENDEDKEY
        
        inp = self._create_key_input(scan_code, flags)
        self._send_input(inp)
        return True
    
    def press_key(self, key: str, duration: float = 0.08):
        """Press and release a key"""
        self.key_down(key)
        time.sleep(duration)
        self.key_up(key)
    
    def hold_key(self, key: str, duration: float):
        """Hold a key for specified duration"""
        self.key_down(key)
        time.sleep(duration)
        self.key_up(key)
    
    def is_key_pressed(self, key: str) -> bool:
        """Check if a key is currently pressed"""
        key_lower = key.lower()
        if key_lower not in VK_CODES:
            return False
        return bool(user32.GetAsyncKeyState(VK_CODES[key_lower]) & 0x8000)
    
    def mouse_move(self, x: int, y: int, absolute: bool = True):
        """Move the mouse cursor"""
        inp = INPUT()
        inp.type = INPUT_MOUSE
        
        if absolute:
            # Convert to normalized coordinates (0-65535)
            screen_width = user32.GetSystemMetrics(0)
            screen_height = user32.GetSystemMetrics(1)
            inp.union.mi.dx = int(x * 65535 / screen_width)
            inp.union.mi.dy = int(y * 65535 / screen_height)
            inp.union.mi.dwFlags = MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE
        else:
            inp.union.mi.dx = x
            inp.union.mi.dy = y
            inp.union.mi.dwFlags = MOUSEEVENTF_MOVE
        
        inp.union.mi.mouseData = 0
        inp.union.mi.time = 0
        inp.union.mi.dwExtraInfo = self._extra
        
        self._send_input(inp)
    
    def mouse_click(self, button: str = 'left', x: Optional[int] = None, y: Optional[int] = None):
        """Click the mouse"""
        if x is not None and y is not None:
            self.mouse_move(x, y)
            time.sleep(0.05)
        
        if button == 'left':
            down_flag = MOUSEEVENTF_LEFTDOWN
            up_flag = MOUSEEVENTF_LEFTUP
        else:
            down_flag = MOUSEEVENTF_RIGHTDOWN
            up_flag = MOUSEEVENTF_RIGHTUP
        
        # Mouse down
        inp = INPUT()
        inp.type = INPUT_MOUSE
        inp.union.mi.dwFlags = down_flag
        inp.union.mi.dwExtraInfo = self._extra
        self._send_input(inp)
        
        time.sleep(0.05)
        
        # Mouse up
        inp.union.mi.dwFlags = up_flag
        self._send_input(inp)
    
    def get_cursor_pos(self) -> tuple:
        """Get current cursor position"""
        point = wintypes.POINT()
        user32.GetCursorPos(ctypes.byref(point))
        return (point.x, point.y)

# Global input handler instance
input_handler = InputHandler()