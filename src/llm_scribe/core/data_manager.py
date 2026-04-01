import json
import os
import threading
import time
from datetime import datetime

from llm_scribe.config import CONFIG_FILE, DEFAULT_DATA_FILE
from llm_scribe.core.security import sanitize_input


class DataManager:
    def __init__(self, config_file=CONFIG_FILE, data_file=DEFAULT_DATA_FILE):
        self.config_file = config_file
        self.data_file = data_file
        self.lock = threading.Lock()
        self.data = {
            "folders": [],
            "sessions": []
        }
        self.load_config()
        self.load_data()

    def load_config(self):
        """Loads configuration from file or creates it if not exists with thread safety."""
        with self.lock:
            if os.path.exists(self.config_file):
                try:
                    with open(self.config_file, encoding="utf-8") as f:
                        config = json.load(f)
                        self.data_file = config.get("data_file", DEFAULT_DATA_FILE)
                except Exception as e:
                    # In a real app, we might want to log this to the shared logger
                    print(f"Error loading config: {e}")
            else:
                # Create default config if not exists as per docstring
                try:
                    config_dir = os.path.dirname(self.config_file)
                    if config_dir:
                        os.makedirs(config_dir, exist_ok=True)
                    with open(self.config_file, "w", encoding="utf-8") as f:
                        json.dump({"data_file": self.data_file}, f, ensure_ascii=False, indent=2)
                except Exception as e:
                    print(f"Error creating config: {e}")

    def save_config(self, new_data_file=None):
        """Saves current configuration to file with thread safety."""
        with self.lock:
            if new_data_file:
                self.data_file = new_data_file
            try:
                config_dir = os.path.dirname(self.config_file)
                if config_dir:
                    os.makedirs(config_dir, exist_ok=True)
                with open(self.config_file, "w", encoding="utf-8") as f:
                    json.dump({"data_file": self.data_file}, f, ensure_ascii=False, indent=2)
            except Exception as e:
                print(f"Error saving config: {e}")

    def load_data(self):
        """Loads sessions and folders from the data file with thread safety."""
        with self.lock:
            if os.path.exists(self.data_file):
                try:
                    with open(self.data_file, encoding="utf-8") as f:
                        loaded = json.load(f)
                        if isinstance(loaded, dict):
                            # Ensure required keys exist for robustness
                            self.data = {
                                "folders": loaded.get("folders", []),
                                "sessions": loaded.get("sessions", [])
                            }
                        else:
                            # Legacy format (list of sessions)
                            self.data = {"folders": [], "sessions": loaded}
                except Exception as e:
                    print(f"Error loading data: {e}")

    def save_data(self):
        """Saves all session and folder data with thread safety."""
        with self.lock:
            try:
                data_dir = os.path.dirname(self.data_file)
                if data_dir:
                    os.makedirs(data_dir, exist_ok=True)
                with open(self.data_file, "w", encoding="utf-8") as f:
                    json.dump(self.data, f, ensure_ascii=False, indent=2)
            except Exception as e:
                print(f"Error saving data: {e}")

    def create_session(self, title, parent_id=""):
        """Creates a new session object and returns its ID."""
        session = {
            "id": str(time.time()),
            "title": sanitize_input(title),
            "content": "",
            "tags": [],
            "parent": parent_id,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        with self.lock:
            self.data["sessions"].append(session)
        self.save_data()
        return session["id"]

    def create_folder(self, name):
        """Creates a new folder object and returns its ID."""
        folder_id = f"folder_{time.time()}"
        with self.lock:
            self.data["folders"].append({"id": folder_id, "name": sanitize_input(name)})
        self.save_data()
        return folder_id

    def update_session(self, sid, content=None, title=None, tags=None, parent=None):
        """Updates an existing session's properties with thread safety."""
        with self.lock:
            for s in self.data["sessions"]:
                if s["id"] == sid:
                    if content is not None:
                        s["content"] = content
                    if title is not None:
                        s["title"] = sanitize_input(title)
                    if tags is not None:
                        s["tags"] = tags
                    if parent is not None:
                        s["parent"] = parent
                    break
        self.save_data()

    def delete_item(self, iid):
        """Deletes a session or folder with thread safety."""
        with self.lock:
            if iid.startswith("folder_"):
                self.data["folders"] = [f for f in self.data["folders"] if f["id"] != iid]
                self.data["sessions"] = [s for s in self.data["sessions"] if s.get("parent") != iid]
            else:
                self.data["sessions"] = [s for s in self.data["sessions"] if s["id"] != iid]
        self.save_data()

    def get_session(self, sid):
        """Retrieves a single session object by its ID with thread safety."""
        with self.lock:
            return next((s for s in self.data["sessions"] if s["id"] == sid), None)

    def rename_item(self, iid, new_name):
        """Renames a folder or session with thread safety."""
        new_name = sanitize_input(new_name)
        with self.lock:
            if iid.startswith("folder_"):
                for f in self.data["folders"]:
                    if f["id"] == iid:
                        f["name"] = new_name
                        break
            else:
                for s in self.data["sessions"]:
                    if s["id"] == iid:
                        s["title"] = new_name
                        break
        self.save_data()
