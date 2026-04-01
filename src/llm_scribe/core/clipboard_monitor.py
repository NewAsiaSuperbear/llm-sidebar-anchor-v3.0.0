import threading
import time
import queue
import ctypes
from datetime import datetime
from llm_scribe.core.security import sanitize_input

# Windows API for thread-safe clipboard access
user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32
CF_UNICODETEXT = 13

# Set explicit argtypes and restypes for 64-bit safety (prevents pointer truncation)
user32.OpenClipboard.argtypes = [ctypes.c_void_p]
user32.OpenClipboard.restype = ctypes.c_bool
user32.GetClipboardData.argtypes = [ctypes.c_uint]
user32.GetClipboardData.restype = ctypes.c_void_p
user32.CloseClipboard.restype = ctypes.c_bool

kernel32.GlobalLock.argtypes = [ctypes.c_void_p]
kernel32.GlobalLock.restype = ctypes.c_void_p
kernel32.GlobalUnlock.argtypes = [ctypes.c_void_p]
kernel32.GlobalUnlock.restype = ctypes.c_bool

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
        except:
            self.root_hwnd = 0

    def _get_clipboard_text(self):
        """
        Extremely robust Win32 clipboard text retrieval.
        Implements retry-fallback, explicit pointer handling, and guaranteed cleanup.
        """
        from utils.logger import logger
        
        # --- PHASE 1: OPEN CLIPBOARD ---
        opened = False
        try:
            # First attempt: Use the specific window handle
            if self.root_hwnd and user32.OpenClipboard(self.root_hwnd):
                opened = True
                logger.debug("ClipboardMonitor: Opened clipboard with root_hwnd.")
            else:
                # Fallback: Wait 10ms and try with 0 (current task)
                time.sleep(0.01)
                if user32.OpenClipboard(0):
                    opened = True
                    logger.debug("ClipboardMonitor: Opened clipboard with fallback (0).")
                else:
                    logger.warning("ClipboardMonitor: Failed to open clipboard (Busy or Locked).")
                    return None
            
            # --- PHASE 2: GET DATA HANDLE ---
            h_clipboard_data = user32.GetClipboardData(CF_UNICODETEXT)
            if not h_clipboard_data:
                # Not an error: clipboard might contain an image or file instead of text
                return None
            
            # --- PHASE 3: LOCK AND COPY MEMORY ---
            p_data = kernel32.GlobalLock(h_clipboard_data)
            if not p_data:
                logger.error("ClipboardMonitor: GlobalLock failed.")
                return None
                
            try:
                # CRITICAL: Use wstring_at to safely read the memory into a Python string.
                # This creates a copy and avoids direct pointer access violations.
                content = ctypes.wstring_at(p_data)
                return content if content else None
            finally:
                # Ensure GlobalLock is always released
                kernel32.GlobalUnlock(h_clipboard_data)
                
        except Exception as e:
            # Catch all low-level memory access or API errors
            logger.error(f"ClipboardMonitor: CRITICAL ACCESS VIOLATION or Error: {e}")
            return None
        finally:
            # --- PHASE 4: GUARANTEED CLEANUP ---
            if opened:
                user32.CloseClipboard()
                logger.debug("ClipboardMonitor: Clipboard closed.")

    def start(self):
        """Starts the clipboard monitoring and processing threads."""
        from utils.logger import logger
        if self.is_active:
            logger.warning("ClipboardMonitor: Already running.")
            return
            
        self.is_active = True
        logger.info("ClipboardMonitor: Starting threads...")
        
        self.monitor_thread = threading.Thread(target=self.poll_loop, daemon=True, name="ClipboardPoller")
        self.monitor_thread.start()
        
        self.processor_thread = threading.Thread(target=self.process_loop, daemon=True, name="ClipboardProcessor")
        self.processor_thread.start()
        logger.info("ClipboardMonitor: Service initialized.")

    def poll_loop(self):
        """Polls the clipboard and pushes new content to the queue."""
        from utils.logger import logger
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

    # safe_poll removed as we're doing it directly in poll_loop for better responsiveness

    def process_loop(self):
        """Background thread: Sanitizes content and triggers UI callback."""
        from utils.logger import logger
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

