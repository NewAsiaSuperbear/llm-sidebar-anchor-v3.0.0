import os
import shutil
import subprocess
import sys
from pathlib import Path


def build():
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)

    print("--- LLM Scribe Pro Build System ---")

    print("Step 1: Cleaning old builds...")
    for folder in ("build", "dist"):
        p = project_root / folder
        if p.exists():
            shutil.rmtree(p)

    print("Step 2: Packaging with PyInstaller...")
    subprocess.check_call(["pyinstaller", "--noconfirm", "LLMScribePro.spec"])

    suffix = ".exe" if sys.platform == "win32" else ""
    print(f"\nSUCCESS: LLMScribePro{suffix} generated in {project_root / 'dist'}")


if __name__ == "__main__":
    build()
