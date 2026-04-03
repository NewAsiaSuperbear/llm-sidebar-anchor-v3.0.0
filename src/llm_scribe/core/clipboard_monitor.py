import queue
import threading
import time
from datetime import datetime

from llm_scribe.core.security import sanitize_input
from llm_scribe.platform.clipboard import get_clipboard_text
from llm_scribe.utils.logger import logger

class ClipboardMonitor:
    def __init__(self, root, on_capture_callback):
        self.root = root
        self.on_capture_callback = on_capture_callback
        self.last_content = ""
        self.is_active = False
        self.monitor_thread = None
        self.content_queue = queue.Queue()
        self.processor_thread = None
        # Cache HWND if possible, though winfo_id is safer when called on demand
        try:
            self.root_hwnd = self.root.winfo_id()
        except Exception:
            self.root_hwnd = 0

    def _get_clipboard_text(self):
        return get_clipboard_text(self.root, self.root_hwnd)

    def start(self):
        """Starts the clipboard monitoring and processing threads."""
        if self.is_active:
            logger.warning("ClipboardMonitor: Already running.")
            return
            
        self.is_active = True
        logger.info("ClipboardMonitor: Starting threads...")
        
        self.monitor_thread = threading.Thread(
            target=self.poll_loop, daemon=True, name="ClipboardPoller"
        )
        self.monitor_thread.start()
        
        self.processor_thread = threading.Thread(
            target=self.process_loop, daemon=True, name="ClipboardProcessor"
        )
        self.processor_thread.start()
        logger.info("ClipboardMonitor: Service initialized.")

    def poll_loop(self):
        """Polls the clipboard and pushes new content to the queue."""
        logger.info("ClipboardMonitor: Poller loop started.")
        while self.is_active:
            try:
                content = self._get_clipboard_text()
                # Ensure we have content and it's different from last capture
                if content is not None and content.strip() != "" and content != self.last_content:
                    logger.info(f"ClipboardMonitor: Detected change (len={len(content)})")
                    self.last_content = content
                    self.content_queue.put({
                        "content": content,
                        "timestamp": datetime.now().strftime("[%H:%M:%S]")
                    })
            except Exception as e:
                logger.error(f"ClipboardMonitor Poll Error: {e}")
            time.sleep(1.0)
        logger.info("ClipboardMonitor: Poller loop stopped.")

    def process_loop(self):
        """Background thread: Sanitizes content and triggers UI callback."""
        while self.is_active:
            try:
                # Wait for content with timeout to check is_active
                data = self.content_queue.get(timeout=1)
                logger.info("ClipboardMonitor: Processing new content...")
                
                # HEAVY LIFTING: Sanitization happens here (off main thread)
                sanitized = sanitize_input(data["content"])
                
                # Schedule the UI update back on the main thread
                # Use after(0) instead of after_idle for more reliable execution
                self.root.after(0, lambda s=sanitized, t=data["timestamp"]: 
                                   self.on_capture_callback(t, s))
                
                self.content_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"ClipboardMonitor Process Error: {e}")

