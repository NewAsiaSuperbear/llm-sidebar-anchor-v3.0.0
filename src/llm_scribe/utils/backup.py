import os
import shutil
from datetime import datetime

from llm_scribe.config import DEFAULT_DATA_FILE


def create_backup():
    """Creates a backup of the current data file."""
    if not os.path.exists(DEFAULT_DATA_FILE):
        return None
    
    backup_dir = os.path.join(os.path.dirname(DEFAULT_DATA_FILE), "backups")
    os.makedirs(backup_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(backup_dir, f"llm_scribe_data_{timestamp}.bak")
    
    try:
        shutil.copy2(DEFAULT_DATA_FILE, backup_path)
        # Keep only last 10 backups
        backups = sorted([os.path.join(backup_dir, f) for f in os.listdir(backup_dir)])
        if len(backups) > 10:
            for b in backups[:-10]:
                os.remove(b)
        return backup_path
    except Exception as e:
        print(f"Backup failed: {e}")
        return None
