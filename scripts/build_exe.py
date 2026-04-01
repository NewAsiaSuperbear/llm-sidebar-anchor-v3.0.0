import subprocess
import sys
import os
import shutil
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
    print("Step 2: Building EXE...")
    try:
        # Use the spec file in the root
        subprocess.check_call(["pyinstaller", "--noconfirm", "LLMScribePro.spec"])
        print(f"\nSUCCESS: LLMScribePro.exe has been generated in {project_root / 'dist'}")
    except Exception as e:
        print(f"\nFAILED: Error during packaging: {e}")

if __name__ == "__main__":
    build()
