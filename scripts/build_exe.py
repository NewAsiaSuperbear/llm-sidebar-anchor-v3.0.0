import os
import sys
import shutil
import subprocess
from pathlib import Path


def build():
    # Move to project root
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    print("--- LLM Scribe Pro Build System ---")
    
    # 1. Clear old build folders
    print("Step 1: Cleaning old builds...")
    folders = ['build', 'dist']
    for folder in folders:
        if (project_root / folder).exists():
            shutil.rmtree(project_root / folder)
            
    # 2. Run PyInstaller
    print("Step 2: Building App...")
    try:
        # Use the spec file in the root
        subprocess.check_call(["pyinstaller", "--noconfirm", "LLMScribePro.spec"])
        ext = "exe" if sys.platform == "win32" else "app" if sys.platform == "darwin" else "bin"
        print(f"\nSUCCESS: LLMScribePro has been generated in {project_root / 'dist'}")
    except Exception as e:
        print(f"\nFAILED: Error during packaging: {e}")

if __name__ == "__main__":
    build()
