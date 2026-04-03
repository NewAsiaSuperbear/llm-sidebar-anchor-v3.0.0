# Config constants for LLM Scribe Pro
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Application metadata
APP_NAME = "LLM Scribe Pro"
VERSION = "2.1.0"

# Determine base paths
# When running as a package, __file__ is in src/llm_scribe/config.py
# Project root is 3 levels up from here (src/llm_scribe/config.py)
PROJECT_ROOT = Path(__file__).parent.parent.parent
ENV_FILE = PROJECT_ROOT / ".env"

# Load environment variables if .env exists
if ENV_FILE.exists():
    load_dotenv(ENV_FILE)

# Colors (Modern Dark Theme)
COLORS = {
    "bg": "#0f0f0f",
    "sidebar": "#121212",
    "card": "#1e1e1e",
    "accent": "#3ea6ff",
    "accent_hover": "#65b8ff",
    "text": "#ffffff",
    "text_dim": "#aaaaaa",
    "border": "#2b2b2b",
    "highlight": "#263850",
    "danger": "#ff4d4d",
    "success": "#2ecc71"
}

# Path management
def get_app_data_dir() -> Path:
    """Determine the application data directory."""
    # Priority: Env Var > APPDATA (Win) > Home Folder
    env_path = os.getenv("LLM_SCRIBE_DATA_DIR")
    if env_path:
        path = Path(env_path).expanduser().resolve()
    elif os.name == 'nt':
        path = Path(os.environ.get('APPDATA', '~')).expanduser() / "LLMScribePro"
    elif sys.platform == 'darwin':
        path = Path("~/Library/Application Support/LLMScribePro").expanduser()
    else:
        path = Path("~/.llm_scribe_pro").expanduser()
    
    path.mkdir(parents=True, exist_ok=True)
    return path

DEFAULT_DATA_DIR = get_app_data_dir()
CONFIG_FILE = DEFAULT_DATA_DIR / "scribe_config.json"
DEFAULT_DATA_FILE = DEFAULT_DATA_DIR / "llm_scribe_data.json"
LOG_FILE = DEFAULT_DATA_DIR / "app.log"
BACKUP_DIR = DEFAULT_DATA_DIR / "backups"
BACKUP_DIR.mkdir(exist_ok=True)

# Security Constants (Loaded from Env)
# Do NOT hardcode the salt in GitHub!
ENCRYPTION_SALT = os.getenv("LLM_SCRIBE_SALT", "default_insecure_salt_change_me")
