"""
Build script for creating a single .EXE with icon
Properly bundles vgamepad DLL files
"""

import subprocess
import sys
import os
import shutil

def find_vgamepad_dlls():
    """Find the vgamepad DLL files"""
    try:
        import vgamepad
        vgamepad_path = os.path.dirname(vgamepad.__file__)
        
        # Find the DLL path
        dll_path = os.path.join(vgamepad_path, "win", "vigem", "client", "x64")
        dll_file = os.path.join(dll_path, "ViGEmClient.dll")
        
        if os.path.exists(dll_file):
            print(f"[+] Found ViGEmClient.dll at: {dll_path}")
            return vgamepad_path
        else:
            print(f"[!] DLL not found at expected path: {dll_file}")
            
            # Search for it
            for root, dirs, files in os.walk(vgamepad_path):
                for file in files:
                    if file.endswith('.dll'):
                        print(f"    Found: {os.path.join(root, file)}")
            
            return vgamepad_path
            
    except ImportError:
        print("[!] vgamepad not installed")
        return None

def create_icon():
    """Create a simple icon file if one doesn't exist"""
    icon_path = "wizard_bot.ico"
    
    if os.path.exists(icon_path):
        print(f"[+] Using existing icon: {icon_path}")
        return icon_path
    
    try:
        from PIL import Image, ImageDraw
        
        size = 256
        img = Image.new('RGBA', (size, size), (157, 140, 255, 255))
        draw = ImageDraw.Draw(img)
        
        # Border
        draw.rectangle([10, 10, size-10, size-10], outline=(26, 26, 46, 255), width=6)
        
        # W shape
        draw.polygon([
            (40, 50), (70, 210), (128, 110), (186, 210), (216, 50),
            (190, 50), (160, 170), (128, 90), (96, 170), (66, 50)
        ], fill=(255, 255, 255, 255))
        
        img.save(icon_path, format='ICO', sizes=[(256, 256), (128, 128), (64, 64), (32, 32), (16, 16)])
        print(f"[+] Created icon: {icon_path}")
        return icon_path
        
    except Exception as e:
        print(f"[!] Could not create icon: {e}")
        return None

def create_spec_file():
    """Create a custom .spec file for PyInstaller"""
    
    vgamepad_path = find_vgamepad_dlls()
    
    spec_content = f'''# -*- mode: python ; coding: utf-8 -*-

import os
import sys

block_cipher = None

# Find vgamepad path
try:
    import vgamepad
    vgamepad_path = os.path.dirname(vgamepad.__file__)
except:
    vgamepad_path = r"{vgamepad_path or ''}"

# Collect vgamepad data files (DLLs)
vgamepad_datas = []
if vgamepad_path and os.path.exists(vgamepad_path):
    for root, dirs, files in os.walk(vgamepad_path):
        for file in files:
            if file.endswith('.dll'):
                src = os.path.join(root, file)
                # Get relative path from vgamepad folder
                rel_dir = os.path.relpath(root, os.path.dirname(vgamepad_path))
                vgamepad_datas.append((src, rel_dir))
                print(f"Adding DLL: {{src}} -> {{rel_dir}}")

a = Analysis(
    ['run.py'],
    pathex=[],
    binaries=vgamepad_datas,
    datas=[
        ('wizard101_bot', 'wizard101_bot'),
    ],
    hiddenimports=[
        'vgamepad',
        'vgamepad.win',
        'vgamepad.win.virtual_gamepad',
        'vgamepad.win.vigem_client',
        'cv2',
        'numpy',
        'PIL',
        'PIL.Image',
        'PIL.ImageGrab',
        'customtkinter',
        'tkinter',
        'ctypes',
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Wizard101BotSuite',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='wizard_bot.ico' if os.path.exists('wizard_bot.ico') else None,
    uac_admin=True,
)
'''
    
    with open('Wizard101BotSuite.spec', 'w') as f:
        f.write(spec_content)
    
    print("[+] Created Wizard101BotSuite.spec")
    return 'Wizard101BotSuite.spec'

def build_exe():
    """Build the executable using PyInstaller"""
    
    # Check/install PyInstaller
    try:
        import PyInstaller
        print("[+] PyInstaller found")
    except ImportError:
        print("[!] Installing PyInstaller...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"])
    
    # Create icon
    create_icon()
    
    # Create spec file
    spec_file = create_spec_file()
    
    # Build
    print("\n[*] Building executable...")
    
    cmd = [sys.executable, "-m", "PyInstaller", "--clean", spec_file]
    print(f"[*] Command: {' '.join(cmd)}")
    
    result = subprocess.run(cmd)
    
    if result.returncode == 0:
        print("\n" + "="*60)
        print("[+] BUILD SUCCESSFUL!")
        print("[+] Executable: dist/Wizard101BotSuite.exe")
        print("="*60)
        
        # Copy images folder if exists
        if os.path.exists("images"):
            dist_images = os.path.join("dist", "images")
            if not os.path.exists(dist_images):
                shutil.copytree("images", dist_images)
                print("[+] Copied images folder to dist/")
        
        # Copy config if exists
        if os.path.exists("config.json"):
            shutil.copy("config.json", os.path.join("dist", "config.json"))
            print("[+] Copied config.json to dist/")
        
        return True
    else:
        print("\n[X] Build failed!")
        return False

if __name__ == "__main__":
    build_exe()