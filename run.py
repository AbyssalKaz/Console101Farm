"""
Launcher script - run this to start the application
"""

import sys
import os

# Add package to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Check dependencies
required_packages = [
    'customtkinter',
    'opencv-python',
    'numpy',
    'Pillow'
]

missing = []
for pkg in required_packages:
    try:
        pkg_name = pkg.replace('-', '_').split('[')[0]
        if pkg_name == 'opencv_python':
            pkg_name = 'cv2'
        elif pkg_name == 'Pillow':
            pkg_name = 'PIL'
        __import__(pkg_name)
    except ImportError:
        missing.append(pkg)

if missing:
    print("Missing required packages:")
    for pkg in missing:
        print(f"  - {pkg}")
    print()
    print("Install with:")
    print(f"  pip install {' '.join(missing)}")
    sys.exit(1)

# Run application
from wizard101_bot.main import main
main()