"""
Main entry point for Wizard101 Bot Suite
"""

import sys
import ctypes

def check_admin():
    """Check if running as administrator"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def main():
    """Main entry point"""
    print("=" * 50)
    print("  Wizard101 Bot Suite")
    print("=" * 50)
    print()
    
    # Check admin
    if not check_admin():
        print("[!] WARNING: Not running as Administrator")
        print("    Some features may not work correctly.")
        print("    Right-click and 'Run as administrator'")
        print()
    
    # Import and run UI
    from .ui import run_app
    run_app()

if __name__ == "__main__":
    main()