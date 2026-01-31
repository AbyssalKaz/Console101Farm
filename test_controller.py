"""Test virtual controller"""

try:
    import vgamepad as vg
    print("[+] vgamepad imported successfully")
    
    print("[*] Creating virtual Xbox controller...")
    gamepad = vg.VX360Gamepad()
    print("[+] Controller created!")
    
    print("[*] Pressing A button...")
    gamepad.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_A)
    gamepad.update()
    
    import time
    time.sleep(0.5)
    
    gamepad.release_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_A)
    gamepad.update()
    print("[+] A button pressed and released!")
    
    print("[*] Moving left stick...")
    gamepad.left_joystick(x_value=32767, y_value=0)
    gamepad.update()
    time.sleep(0.5)
    
    gamepad.left_joystick(x_value=0, y_value=0)
    gamepad.update()
    print("[+] Left stick moved!")
    
    print("")
    print("=" * 50)
    print("[+] SUCCESS! Virtual controller is working!")
    print("=" * 50)
    
    del gamepad
    
except Exception as e:
    print(f"[X] Error: {e}")
    print("")
    print("Make sure:")
    print("1. ViGEmBus is installed (restart after installing)")
    print("2. vgamepad is installed: pip install vgamepad")