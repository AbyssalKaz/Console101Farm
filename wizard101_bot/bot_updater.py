"""
Auto-updater for Wizard101 Bot Suite
Downloads updates from GitHub repository
"""

import os
import sys
import json
import shutil
import zipfile
import tempfile
import threading
from typing import Optional, Callable, Tuple
from urllib.request import urlopen, Request
from urllib.error import URLError

# GitHub repository info
GITHUB_OWNER = "YourUsername"  # Change this to your GitHub username
GITHUB_REPO = "Wizard101BotSuite"  # Change this to your repo name
GITHUB_BRANCH = "main"

# Version info
CURRENT_VERSION = "1.0.0"
VERSION_FILE = "version.json"

class AutoUpdater:
    """
    Auto-updater that checks GitHub for updates and downloads them.
    """
    
    def __init__(self):
        self.github_owner = GITHUB_OWNER
        self.github_repo = GITHUB_REPO
        self.github_branch = GITHUB_BRANCH
        self.current_version = self._load_current_version()
        
        self._log_callback: Optional[Callable[[str], None]] = None
        self._update_available = False
        self._latest_version = None
        self._download_url = None
    
    def set_log_callback(self, callback: Callable[[str], None]):
        self._log_callback = callback
    
    def _log(self, message: str):
        print(message)
        if self._log_callback:
            self._log_callback(message)
    
    def _load_current_version(self) -> str:
        """Load current version from version.json"""
        try:
            if os.path.exists(VERSION_FILE):
                with open(VERSION_FILE, 'r') as f:
                    data = json.load(f)
                    return data.get('version', CURRENT_VERSION)
        except:
            pass
        return CURRENT_VERSION
    
    def _save_current_version(self, version: str):
        """Save current version to version.json"""
        try:
            with open(VERSION_FILE, 'w') as f:
                json.dump({'version': version}, f)
        except Exception as e:
            self._log(f"[!] Failed to save version: {e}")
    
    def get_api_url(self) -> str:
        """Get GitHub API URL for releases"""
        return f"https://api.github.com/repos/{self.github_owner}/{self.github_repo}/releases/latest"
    
    def get_raw_url(self, path: str) -> str:
        """Get raw GitHub URL for a file"""
        return f"https://raw.githubusercontent.com/{self.github_owner}/{self.github_repo}/{self.github_branch}/{path}"
    
    def get_zip_url(self) -> str:
        """Get URL to download the repo as a zip"""
        return f"https://github.com/{self.github_owner}/{self.github_repo}/archive/refs/heads/{self.github_branch}.zip"
    
    def check_for_updates(self) -> Tuple[bool, Optional[str]]:
        """
        Check GitHub for updates.
        
        Returns: (update_available, latest_version)
        """
        self._log("[*] Checking for updates...")
        
        try:
            # Try to get latest release info
            version_url = self.get_raw_url(VERSION_FILE)
            req = Request(version_url, headers={'User-Agent': 'Wizard101BotSuite'})
            
            with urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())
                latest_version = data.get('version', CURRENT_VERSION)
            
            self._latest_version = latest_version
            
            if self._compare_versions(latest_version, self.current_version) > 0:
                self._update_available = True
                self._log(f"[+] Update available: {self.current_version} -> {latest_version}")
                return True, latest_version
            else:
                self._log(f"[+] Already up to date (v{self.current_version})")
                return False, self.current_version
                
        except URLError as e:
            self._log(f"[!] Could not check for updates: {e}")
            return False, None
        except Exception as e:
            self._log(f"[!] Update check error: {e}")
            return False, None
    
    def _compare_versions(self, v1: str, v2: str) -> int:
        """
        Compare two version strings.
        Returns: 1 if v1 > v2, -1 if v1 < v2, 0 if equal
        """
        try:
            parts1 = [int(x) for x in v1.split('.')]
            parts2 = [int(x) for x in v2.split('.')]
            
            for i in range(max(len(parts1), len(parts2))):
                p1 = parts1[i] if i < len(parts1) else 0
                p2 = parts2[i] if i < len(parts2) else 0
                
                if p1 > p2:
                    return 1
                elif p1 < p2:
                    return -1
            
            return 0
        except:
            return 0
    
    def download_update(self, progress_callback: Optional[Callable[[int, int], None]] = None) -> bool:
        """
        Download the latest version from GitHub.
        
        Args:
            progress_callback: Optional callback(downloaded_bytes, total_bytes)
            
        Returns: True if successful
        """
        self._log("[*] Downloading update...")
        
        try:
            zip_url = self.get_zip_url()
            req = Request(zip_url, headers={'User-Agent': 'Wizard101BotSuite'})
            
            # Create temp directory
            temp_dir = tempfile.mkdtemp()
            zip_path = os.path.join(temp_dir, "update.zip")
            
            # Download
            with urlopen(req, timeout=60) as response:
                total_size = int(response.headers.get('content-length', 0))
                downloaded = 0
                
                with open(zip_path, 'wb') as f:
                    while True:
                        chunk = response.read(8192)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if progress_callback:
                            progress_callback(downloaded, total_size)
            
            self._log(f"[+] Downloaded {downloaded} bytes")
            
            # Extract
            self._log("[*] Extracting update...")
            extract_dir = os.path.join(temp_dir, "extracted")
            
            with zipfile.ZipFile(zip_path, 'r') as z:
                z.extractall(extract_dir)
            
            # Find the extracted folder (GitHub adds repo-branch suffix)
            extracted_folders = os.listdir(extract_dir)
            if not extracted_folders:
                raise Exception("No files extracted")
            
            source_dir = os.path.join(extract_dir, extracted_folders[0])
            
            # Apply update
            return self._apply_update(source_dir)
            
        except Exception as e:
            self._log(f"[X] Download failed: {e}")
            return False
    
    def _apply_update(self, source_dir: str) -> bool:
        """
        Apply the downloaded update.
        Copies new files over existing ones.
        """
        self._log("[*] Applying update...")
        
        try:
            # Files/folders to update
            items_to_update = [
                "wizard101_bot",
                "run.py",
                "version.json",
            ]
            
            current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            
            for item in items_to_update:
                src = os.path.join(source_dir, item)
                dst = os.path.join(current_dir, item)
                
                if os.path.exists(src):
                    if os.path.isdir(src):
                        # Remove existing directory
                        if os.path.exists(dst):
                            shutil.rmtree(dst)
                        shutil.copytree(src, dst)
                        self._log(f"    Updated folder: {item}")
                    else:
                        shutil.copy2(src, dst)
                        self._log(f"    Updated file: {item}")
            
            # Update version
            if self._latest_version:
                self._save_current_version(self._latest_version)
                self.current_version = self._latest_version
            
            self._log("[+] Update applied successfully!")
            self._log("[!] Please restart the application.")
            
            return True
            
        except Exception as e:
            self._log(f"[X] Failed to apply update: {e}")
            return False
    
    def check_and_update_async(self, callback: Optional[Callable[[bool, str], None]] = None):
        """
        Check for updates in a background thread.
        
        Args:
            callback: Called with (update_applied, message)
        """
        def _run():
            available, version = self.check_for_updates()
            
            if available:
                if callback:
                    callback(False, f"Update available: {version}")
            else:
                if callback:
                    callback(False, f"Up to date: v{self.current_version}")
        
        thread = threading.Thread(target=_run, daemon=True)
        thread.start()

# Global instance
updater = AutoUpdater()