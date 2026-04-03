import subprocess
import sys
from pathlib import Path


if __name__ == "__main__":
    subprocess.check_call([sys.executable, str(Path(__file__).with_name("build_dist.py"))])
