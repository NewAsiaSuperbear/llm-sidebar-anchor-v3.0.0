import os
import tkinter as tk
from tkinter import messagebox, scrolledtext, simpledialog, ttk

import customtkinter as ctk

from llm_scribe.config import APP_NAME, COLORS, VERSION
from llm_scribe.core.clipboard_monitor import ClipboardMonitor
from llm_scribe.core.data_manager import DataManager
from llm_scribe.core.exporter import Exporter
from llm_scribe.core.security import sanitize_input
from llm_scribe.platform.window_features import set_click_through, supports_click_through
from llm_scribe.ui.components import StatusIndicator, Toast
from llm_scribe.ui.export_dialog import ExportDialog
from llm_scribe.ui.move_dialog import MoveDialog
from llm_scribe.ui.styles import AppStyles
from llm_scribe.ui.wizard import FirstRunWizard
from llm_scribe.utils.backup import create_backup
from llm_scribe.utils.logger import logger, perf_log


class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        logger.info(f"Starting {APP_NAME} v{VERSION}...")
        self._ghost_update_job = None  # For debouncing
        self.setup_window()
        self.init_core()
        self.setup_ui()
        self.start_services()
        self.check_first_run()

    def setup_window(self):
        """Configures the main window basic properties."""
        self.title(f"{APP_NAME} v{VERSION}")
        self.geometry("1100x720")
        self.minsize(950, 600)
        self.configure(fg_color=COLORS["bg"])
        self.attributes("-alpha", 1.0) # Ensure layered window style is initialized
        AppStyles.setup_theme()
        self.fonts = AppStyles.get_fonts()

    def init_core(self):
        """Initializes data management and state variables."""
        self.data_manager = DataManager()
        self.exporter = Exporter(self.data_manager)
        self.current_session_id = None
        self.is_scribe_mode = tk.BooleanVar(value=False)
        self.is_always_on_top = tk.BooleanVar(value=False)
        self.is_click_through = tk.BooleanVar(value=False)
        self.opacity = tk.DoubleVar(value=1.0)

    def setup_ui(self):
        """Builds the main user interface layout."""
        # --- HEADER ---
        self.header = ctk.CTkFrame(self, height=60, corner_radius=0, fg_color=COLORS["sidebar"])
        self.header.pack(side=ctk.TOP, fill=ctk.X)
        
        self.title_label = ctk.CTkLabel(self.header, text=f"▶ {APP_NAME}", font=self.fonts["title"], text_color=COLORS["text"])
        self.title_label.pack(side=ctk.LEFT, padx=20)
        
        # Search Bar
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *args: self.perform_search())
        self.search_entry = ctk.CTkEntry(
            self.header, placeholder_text="🔍 搜索 (Search)...", 
            width=250, font=self.fonts["main"], textvariable=self.search_var
        )
        self.search_entry.pack(side=ctk.LEFT, padx=20)

        # Scribe Toggle
        self.scribe_btn = ctk.CTkButton(
            self.header, text="🚀 速记 (Scribe) OFF", font=self.fonts["bold"], 
            fg_color=COLORS["card"], text_color=COLORS["text"], width=140,
            command=self.toggle_scribe_mode
        )
        self.scribe_btn.pack(side=ctk.LEFT, padx=5)
        
        # Status Indicator
        self.status_led = StatusIndicator(self.header)
        self.status_led.pack(side=ctk.LEFT, padx=5)

        # Right Header Controls
        self.controls_frame = ctk.CTkFrame(self.header, fg_color="transparent")
        self.controls_frame.pack(side=ctk.RIGHT, padx=15)
        
        # Backup Button
        self.backup_btn = ctk.CTkButton(
            self.controls_frame, text="💾 备份", font=self.fonts["small"], 
            width=60, fg_color=COLORS["card"], command=self.manual_backup
        )
        self.backup_btn.pack(side=ctk.LEFT, padx=5)

        # Guide Button
        self.guide_btn = ctk.CTkButton(
            self.controls_frame, text="❓ 指南", font=self.fonts["small"], 
            width=60, fg_color=COLORS["card"], command=self.show_usage_guide
        )
        self.guide_btn.pack(side=ctk.LEFT, padx=5)

        # Opacity Slider
        self.opacity_slider = ctk.CTkSlider(
            self.controls_frame, from_=0.2, to=1.0, width=80,
            variable=self.opacity, command=self.update_opacity
        )
        self.opacity_slider.pack(side=ctk.LEFT, padx=5)

        self.pin_btn = ctk.CTkCheckBox(
            self.controls_frame, text="📌 置顶", font=self.fonts["small"], 
            variable=self.is_always_on_top, command=self.toggle_always_on_top
        )
        self.pin_btn.pack(side=ctk.LEFT, padx=5)
        
        # Ghost Mode removed for stability (temporarily)
        # self.ghost_btn = ctk.CTkCheckBox(
        #     self.controls_frame, text="👻 穿透", font=self.fonts["small"], 
        #     variable=self.is_click_through, command=self.toggle_click_through
        # )
        # self.ghost_btn.pack(side=ctk.LEFT, padx=5)

        # --- BODY ---
        self.body = ctk.CTkFrame(self, fg_color="transparent")
        self.body.pack(fill=ctk.BOTH, expand=True)

        # Sidebar (Left)
        self.sidebar = ctk.CTkFrame(self.body, width=280, corner_radius=0, fg_color=COLORS["sidebar"])
        self.sidebar.pack(side=ctk.LEFT, fill=ctk.Y)
        self.sidebar.pack_propagate(False)
        
        self.lib_label = ctk.CTkLabel(self.sidebar, text="📚 库 (Library)", font=self.fonts["bold"], text_color=COLORS["text"])
        self.lib_label.pack(anchor="w", padx=20, pady=(15, 10))
        
        self.sidebar_btns = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.sidebar_btns.pack(fill=ctk.X, padx=15, pady=5)
        
        self.new_session_btn = ctk.CTkButton(
            self.sidebar_btns, text="+ 新建 (New)", font=self.fonts["bold"], 
            fg_color=COLORS["accent"], width=110, command=self.create_new_session
        )
        self.new_session_btn.pack(side=ctk.LEFT, padx=2)
        
        self.new_folder_btn = ctk.CTkButton(
            self.sidebar_btns, text="📁 归档 (Folder)", font=self.fonts["bold"], 
            fg_color=COLORS["card"], width=110, command=self.create_folder
        )
        self.new_folder_btn.pack(side=tk.LEFT, padx=2)

        # Treeview (using standard ttk for hierarchical view)
        self.setup_treeview()

        # Center (Main Content)
        self.center = ctk.CTkFrame(self.body, fg_color="transparent")
        self.center.pack(side=ctk.LEFT, fill=ctk.BOTH, expand=True, padx=15, pady=15)
        
        self.session_title_var = tk.StringVar(value="请选择会话 (Select Session)")
        self.session_label = ctk.CTkLabel(self.center, textvariable=self.session_title_var, font=self.fonts["title"])
        self.session_label.pack(anchor="w", pady=(0, 10))
        
        self.text_card = ctk.CTkFrame(self.center, fg_color=COLORS["card"], border_color=COLORS["border"], border_width=1)
        self.text_card.pack(fill=ctk.BOTH, expand=True)
        
        self.dialog_text = scrolledtext.ScrolledText(
            self.text_card, wrap=tk.WORD, font=self.fonts["mono"], bg=COLORS["card"], fg=COLORS["text"],
            insertbackground="white", relief=tk.FLAT, padx=20, pady=20, undo=True
        )
        self.dialog_text.pack(fill=tk.BOTH, expand=True)
        self.dialog_text.tag_configure("timestamp", foreground=COLORS["accent"], font=("Consolas", 10, "bold"))
        self.dialog_text.tag_configure("highlight", background=COLORS["highlight"])

        # Right (Tags/Bookmarks)
        self.right_panel = ctk.CTkFrame(self.body, width=280, corner_radius=0, fg_color=COLORS["sidebar"])
        self.right_panel.pack(side=ctk.RIGHT, fill=ctk.Y)
        self.right_panel.pack_propagate(False)
        
        self.tags_label = ctk.CTkLabel(self.right_panel, text="📌 书签 (Bookmarks)", font=self.fonts["bold"], text_color=COLORS["text"])
        self.tags_label.pack(anchor="w", padx=20, pady=(15, 10))
        
        self.tag_list = tk.Listbox(
            self.right_panel, bg=COLORS["card"], fg=COLORS["text"], font=self.fonts["main"], 
            bd=0, highlightthickness=0, selectbackground=COLORS["accent"]
        )
        self.tag_list.pack(fill=ctk.BOTH, expand=True, padx=15, pady=5)
        self.tag_list.bind("<Double-Button-1>", self.jump_to_tag)
        
        self.tag_input_frame = ctk.CTkFrame(self.right_panel, fg_color="transparent")
        self.tag_input_frame.pack(fill=ctk.X, padx=15, pady=10)
        self.tag_entry = ctk.CTkEntry(self.tag_input_frame, placeholder_text="书签名称...", font=self.fonts["main"])
        self.tag_entry.pack(fill=ctk.X, pady=5)
        self.add_tag_btn = ctk.CTkButton(self.tag_input_frame, text="🔖 添加书签 (Add)", font=self.fonts["bold"], command=self.add_manual_tag)
        self.add_tag_btn.pack(fill=ctk.X)

    def setup_treeview(self):
        """Hierarchical treeview for folders and sessions."""
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background=COLORS["sidebar"], foreground=COLORS["text_dim"], 
                        fieldbackground=COLORS["sidebar"], borderwidth=0, font=self.fonts["main"])
        style.map("Treeview", background=[('selected', COLORS["highlight"])], foreground=[('selected', 'white')])
        
        self.tree = ttk.Treeview(self.sidebar, show="tree", selectmode="browse")
        self.tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)
        
        # Context Menu
        self.sidebar_menu = tk.Menu(self, tearoff=0, bg=COLORS["card"], fg=COLORS["text"])
        self.sidebar_menu.add_command(label="📝 重命名 (Rename)", command=self.rename_item)
        self.sidebar_menu.add_command(label="📁 移动到 (Move to)", command=self.move_item)
        self.sidebar_menu.add_command(label="📤 导出 (Export)", command=self.export_item)
        self.sidebar_menu.add_command(label="🗑️ 删除 (Delete)", command=self.delete_item, foreground=COLORS["danger"])
        self.tree.bind("<Button-3>", lambda e: self.sidebar_menu.post(e.x_root, e.y_root))
        
        # INITIAL REFRESH
        self.refresh_tree()

    @perf_log
    def perform_search(self):
        """Performs real-time search across session titles and content with error handling."""
        try:
            query = self.search_var.get().lower()
            if not query:
                self.refresh_tree()
                return

            # Clear current tree
            self.tree.delete(*self.tree.get_children())
            
            # Search in data manager
            with self.data_manager.lock:
                for s in self.data_manager.data["sessions"]:
                    if query in s["title"].lower() or query in s["content"].lower():
                        self.tree.insert("", "end", iid=s["id"], text=f"🔍 {s['title']}")
        except Exception as e:
            logger.error(f"Search failed: {e}")
            Toast(self, "搜索出错 (Search Error)", fg_color=COLORS["danger"]).show()

    def manual_backup(self):
        """Triggers a manual backup with toast notification."""
        path = create_backup()
        if path:
            Toast(self, f"备份成功！\n{os.path.basename(path)}").show()
            logger.info(f"Manual backup created: {path}")
        else:
            Toast(self, "备份失败", fg_color=COLORS["danger"]).show()

    def show_usage_guide(self):
        """Displays a popup window with the usage guide in Chinese and English."""
        guide_window = ctk.CTkToplevel(self)
        guide_window.title("使用指南 (Usage Guide)")
        guide_window.geometry("600x500")
        guide_window.configure(fg_color=COLORS["bg"])
        guide_window.attributes("-topmost", True)
        
        # Header
        header_text = "LLM Scribe Pro 使用指南 (Guide)"
        header = ctk.CTkLabel(guide_window, text=header_text, font=self.fonts["title"])
        header.pack(pady=20)
        
        # Scrollable Content
        content_frame = ctk.CTkFrame(guide_window, fg_color=COLORS["sidebar"], corner_radius=10)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        
        guide_text = scrolledtext.ScrolledText(
            content_frame, wrap=tk.WORD, font=self.fonts["main"], 
            bg=COLORS["sidebar"], fg=COLORS["text"], bd=0, padx=15, pady=15
        )
        guide_text.pack(fill=tk.BOTH, expand=True)
        
        text = """
LLM Scribe Pro v2.x - Usage Guide / 使用指南

--- 1. Scribe Mode / 速记模式 ---
[EN] Toggle the '🚀 Scribe' button to 'ON'. The app will automatically capture anything you copy to your clipboard and append it to the current session with a timestamp.
[CN] 开启顶部的 '🚀 速记' 按钮为 'ON'. 程序将自动捕捉您复制到剪贴板的任何内容, 并带上时间戳记录到当前会话中。

--- 2. Sessions & Folders / 会话与文件夹 ---
[EN] Use '📄 New Session' to start a fresh dialogue log. Use '📁 Folder' to categorize and group your sessions. You can drag and drop (planned) or move items using the context menu.
[CN] 点击 '📄 新建' 开始一段新的对话记录。点击 '📁 归档' 创建文件夹, 帮助您分类管理不同的项目。

--- 3. Real-time Search / 实时搜索 ---
[EN] Type in the search bar to instantly filter sessions by title or content. The list will update as you type.
[CN] 在搜索框输入关键词, 程序会实时根据标题或内容过滤会话。

--- 4. Bookmarks / 书签 ---
[EN] In any session, type a name in the bookmark field and click '🔖 Add'. Double-click a bookmark in the right panel to instantly jump to that position.
[CN] 在会话中, 输入书签名称并点击 '🔖 添加'. 双击右侧面板中的书签, 即可快速跳转到文本中的对应位置。

--- 5. Opacity & Pin / 透明度与置顶 ---
[EN] Use the slider to adjust window transparency. Use the '📌 Pin' checkbox to keep the window always on top of other applications.
[CN] 使用滑动条调整窗口透明度。勾选 '📌 置顶' 可使窗口始终保持在其他应用程序上方。

--- 6. Security & Data / 安全与数据 ---
[EN] All data is encrypted and stored locally in your system application data directory (Windows: AppData, macOS: Application Support, Linux: XDG data dir).
No data is sent to external servers. Use '💾 Backup' regularly to save snapshots of your data.
[CN] 所有数据均经过加密并存储在本地系统应用数据目录中（Windows: AppData，macOS: Application Support，Linux: XDG 数据目录）。
数据不会上传到外部服务器。请定期使用 '💾 备份' 功能保存数据快照。
        """
        guide_text.insert(tk.END, text.strip())
        guide_text.configure(state=tk.DISABLED) # Read-only
        
        # Close Button
        close_btn = ctk.CTkButton(guide_window, text="关闭 (Close)", command=guide_window.destroy)
        close_btn.pack(pady=10)

    def update_opacity(self, value):
        """Adjusts window transparency using standard Tkinter method."""
        self.attributes("-alpha", float(value))
        # No need to call apply_click_through here, as alpha doesn't change click-through status

    def toggle_click_through(self):
        """Enables/disables click-through for Ghost Mode with debouncing."""
        if self._ghost_update_job:
            self.after_cancel(self._ghost_update_job)
        self._ghost_update_job = self.after(50, self._do_toggle_click_through)

    def _do_toggle_click_through(self):
        """Actual API call to toggle click-through."""
        self.apply_click_through(self.is_click_through.get())
        self._ghost_update_job = None

    def apply_click_through(self, enable):
        try:
            if not supports_click_through():
                if enable:
                    Toast(self, "当前系统不支持穿透模式", fg_color=COLORS["danger"], duration=2000).show()
                return

            ok = set_click_through(self, enable)
            if not ok:
                Toast(self, "穿透模式设置失败", fg_color=COLORS["danger"], duration=2000).show()
                return

            status = "ON" if enable else "OFF"
            logger.info(f"Ghost Mode (Click-Through) turned {status}")
            if enable:
                Toast(self, "穿透模式已开启 (Ghost Mode ON)", duration=1500).show()
            else:
                Toast(self, "穿透模式已关闭 (Ghost Mode OFF)", duration=1500).show()
        except Exception as e:
            logger.error(f"Click-through failed: {e}")

    def start_services(self):
        """Starts background tasks and monitoring services."""
        self.monitor = ClipboardMonitor(self, self.on_clipboard_captured)
        self.monitor.start()
        # Auto-save every 30 seconds
        self.auto_save()

    def auto_save(self):
        """Periodically saves data to disk."""
        self.save_current_session()
        self.data_manager.save_data()
        self.after(30000, self.auto_save)

    def check_first_run(self):
        """Checks if it's the first run to show the wizard."""
        if not os.path.exists(self.data_manager.config_file):
            self.after(500, lambda: FirstRunWizard(self, self.on_wizard_complete))

    def on_wizard_complete(self):
        """Handles completion of the first-run wizard."""
        self.data_manager.save_config()
        Toast(self, "向导完成! 开启速记之旅吧。", duration=3000).show()

    def toggle_scribe_mode(self):
        new_state = not self.is_scribe_mode.get()
        self.is_scribe_mode.set(new_state)
        self.status_led.set_status(new_state)
        self.scribe_btn.configure(
            fg_color=COLORS["accent"] if new_state else COLORS["card"],
            text=f"🚀 速记 (Scribe) {'ON' if new_state else 'OFF'}"
        )
        if new_state:
            Toast(self, "速记模式已开启 (Scribe Mode ON)").show()

    @perf_log
    def on_clipboard_captured(self, timestamp, content):
        """Callback when clipboard content is captured with thread safety."""
        def update_ui():
            try:
                if not self.is_scribe_mode.get():
                    return
                
                sanitized = sanitize_input(content.strip())
                if not sanitized:
                    return

                logger.info(f"CAPTURED: {sanitized[:30]}...")
                
                if self.current_session_id is None:
                    self.create_new_session("自动捕获 (Auto Capture)")
                
                # Append content to the editor
                self.dialog_text.insert(tk.END, f"\n{timestamp} ", "timestamp")
                self.dialog_text.insert(tk.END, f"{sanitized}\n")
                self.dialog_text.see(tk.END)
                self.save_current_session()
                
                Toast(self, "已记录内容 (Captured)", duration=1500).show()
            except Exception as e:
                logger.error(f"Error updating UI with clipboard content: {e}")
        
        # Schedule UI update on the main thread to ensure thread safety
        self.after(0, update_ui)

    def toggle_always_on_top(self):
        self.attributes("-topmost", self.is_always_on_top.get())

    def create_new_session(self, title=None):
        if not title:
            prompt_title = "新建会话 (New Session)"
            prompt_msg = "请输入会话名称 (Enter Name):"
            default_name = f"会话 {len(self.data_manager.data['sessions'])+1}"
            title = simpledialog.askstring(prompt_title, prompt_msg) or default_name
        
        sid = self.data_manager.create_session(title)
        self.refresh_tree()
        self.select_session(sid)

    def create_folder(self):
        prompt_title = "新建文件夹 (New Folder)"
        prompt_msg = "请输入文件夹名称 (Folder Name):"
        default_name = "新归档 (New Folder)"
        name = simpledialog.askstring(prompt_title, prompt_msg) or default_name
        self.data_manager.create_folder(name)
        self.refresh_tree()

    @perf_log
    def refresh_tree(self):
        """Optimized Treeview update using incremental refresh with thread safety."""
        try:
            with self.data_manager.lock:
                # 1. 获取当前 Treeview 中所有的节点
                existing_iids = self._get_existing_tree_iids()
                
                # 2. 更新文件夹并获取活跃的文件夹 ID
                active_folder_iids = self._refresh_folders()
                
                # 3. 更新会话并获取活跃的会话 ID
                active_session_iids = self._refresh_sessions()
                
                # 4. 清理不再存在的数据节点
                active_all_iids = active_folder_iids.union(active_session_iids)
                self._cleanup_tree(existing_iids, active_all_iids)
                
        except Exception as e:
            logger.error(f"Failed to refresh tree: {e}")

    def _get_existing_tree_iids(self):
        """Helper to recursively get all current item IDs in the tree."""
        existing_iids = set()
        def get_all_children(parent=""):
            children = self.tree.get_children(parent)
            for child in children:
                existing_iids.add(child)
                get_all_children(child)
        
        get_all_children()
        return existing_iids

    def _refresh_folders(self):
        """Helper to update folder nodes and return active folder IDs."""
        active_folder_iids = set()
        for f in self.data_manager.data["folders"]:
            fid = f["id"]
            active_folder_iids.add(fid)
            text = f"📁 {f['name']}"
            
            if self.tree.exists(fid):
                if self.tree.item(fid, "text") != text:
                    self.tree.item(fid, text=text)
            else:
                self.tree.insert("", "end", iid=fid, text=text)
        return active_folder_iids

    def _refresh_sessions(self):
        """Helper to update session nodes and return active session IDs."""
        active_session_iids = set()
        for s in self.data_manager.data["sessions"]:
            sid = s["id"]
            active_session_iids.add(sid)
            text = f"📄 {s['title']}"
            parent = s.get("parent", "")
            
            # Ensure parent is valid or set to root
            if parent and not self.tree.exists(parent):
                parent = ""
            
            if self.tree.exists(sid):
                # Check if item needs to move parent or update text
                current_parent = self.tree.parent(sid)
                if current_parent != parent or self.tree.item(sid, "text") != text:
                    self.tree.move(sid, parent, "end")
                    self.tree.item(sid, text=text)
            else:
                self.tree.insert(parent, "end", iid=sid, text=text)
        return active_session_iids

    def _cleanup_tree(self, existing_iids, active_all_iids):
        """Helper to remove tree items that no longer exist in data."""
        for iid in existing_iids:
            if iid not in active_all_iids:
                if self.tree.exists(iid):
                    self.tree.delete(iid)

    def on_tree_select(self, event):
        selection = self.tree.selection()
        if selection:
            iid = selection[0]
            if not iid.startswith("folder_") and iid != self.current_session_id:
                self.select_session(iid)

    def select_session(self, sid):
        """Selects a session and loads its content with error handling."""
        try:
            if self.current_session_id:
                self.save_current_session()
            
            self.current_session_id = sid
            session = self.data_manager.get_session(sid)
            if session:
                self.session_title_var.set(session["title"])
                self.dialog_text.delete("1.0", tk.END)
                self.dialog_text.insert("1.0", session["content"])
                self.refresh_tag_list()
                # Ensure tree selection matches sid without triggering a new select event
                current_selection = self.tree.selection()
                if not current_selection or current_selection[0] != sid:
                    self.tree.selection_set(sid)
                    self.tree.see(sid)
            else:
                logger.warning(f"Session {sid} not found during selection.")
        except Exception as e:
            logger.error(f"Failed to select session {sid}: {e}")
            Toast(self, "加载会话失败 (Load Failed)", fg_color=COLORS["danger"]).show()

    @perf_log
    def save_current_session(self):
        """Saves current session content with error handling."""
        try:
            if self.current_session_id:
                content = self.dialog_text.get("1.0", tk.END).strip()
                self.data_manager.update_session(self.current_session_id, content=content)
        except Exception as e:
            logger.error(f"Failed to save current session: {e}")

    def rename_item(self):
        """Renames the selected session or folder with thread safety."""
        try:
            selection = self.tree.selection()
            if not selection:
                return
            iid = selection[0]
            new_name = simpledialog.askstring("重命名 (Rename)", "输入新名称 (Enter New Name):")
            if new_name:
                self.data_manager.rename_item(iid, new_name)
                self.refresh_tree()
                Toast(self, "重命名成功!").show()
        except Exception as e:
            logger.error(f"Rename failed: {e}")

    def move_item(self):
        """Triggers the move flow for the selected session."""
        selection = self.tree.selection()
        if not selection:
            return
        iid = selection[0]
        
        # We only support moving sessions, not folders (yet)
        if iid.startswith("folder_"):
            Toast(self, "暂不支持移动文件夹 (Folders cannot be moved)", 
                  fg_color=COLORS["danger"]).show()
            return
        
        def do_move(target_folder_id):
            self.data_manager.update_session(iid, parent=target_folder_id)
            self.refresh_tree()
            Toast(self, "移动成功 (Moved)").show()

        MoveDialog(self, self.data_manager.data["folders"], on_confirm=do_move)

    def export_item(self):
        """Triggers the export flow for the selected session or folder."""
        selection = self.tree.selection()
        if not selection:
            return
        iid = selection[0]
        
        is_folder = iid.startswith("folder_")
        item_text = self.tree.item(iid, "text").strip()
        # Remove icons from text
        item_name = item_text.replace("📁 ", "").replace("📄 ", "")
        
        def do_export(fmt, path, preset=None):
            if is_folder:
                count = self.exporter.export_folder(iid, path, format=fmt, preset=preset)
                if count > 0:
                    Toast(self, f"成功导出 {count} 个文件").show()
                else:
                    Toast(self, "导出失败", fg_color=COLORS["danger"]).show()
            else:
                success = self.exporter.export_session(iid, path, format=fmt, preset=preset)
                if success:
                    Toast(self, "导出成功 (Exported)").show()
                else:
                    Toast(self, "导出失败", fg_color=COLORS["danger"]).show()

        ExportDialog(self, item_name, is_folder=is_folder, on_confirm=do_export)

    def delete_item(self):
        """Deletes a tree item with error handling."""
        try:
            selection = self.tree.selection()
            if not selection:
                return
            iid = selection[0]
            if messagebox.askyesno("确认删除 (Delete)", "确定要删除该项目吗?"):
                self.data_manager.delete_item(iid)
                if iid == self.current_session_id:
                    self.current_session_id = None
                    self.dialog_text.delete("1.0", tk.END)
                    self.session_title_var.set("已选择 (None)")
                self.refresh_tree()
        except Exception as e:
            logger.error(f"Delete failed: {e}")

    def add_manual_tag(self):
        """Adds a tag to the current session with error handling."""
        try:
            name = self.tag_entry.get().strip()
            if not name or not self.current_session_id:
                return
            pos = self.dialog_text.index(tk.INSERT)
            session = self.data_manager.get_session(self.current_session_id)
            if session:
                session["tags"].append({"name": sanitize_input(name), "pos": pos})
                self.data_manager.save_data()
                self.tag_entry.delete(0, "end")
                self.refresh_tag_list()
                Toast(self, "书签已添加 (Bookmark Added)").show()
        except Exception as e:
            logger.error(f"Failed to add tag: {e}")

    def refresh_tag_list(self):
        self.tag_list.delete(0, tk.END)
        session = self.data_manager.get_session(self.current_session_id)
        if session:
            for t in session["tags"]:
                self.tag_list.insert(tk.END, f"📍 {t['name']}")

    def jump_to_tag(self, event):
        selection = self.tag_list.curselection()
        if selection and self.current_session_id:
            idx = selection[0]
            session = self.data_manager.get_session(self.current_session_id)
            if session and idx < len(session["tags"]):
                tag = session["tags"][idx]
                self.dialog_text.tag_remove("highlight", "1.0", tk.END)
                try:
                    self.dialog_text.see(tag["pos"])
                    line = tag["pos"].split('.')[0]
                    self.dialog_text.tag_add("highlight", f"{line}.0", f"{line}.end")
                except Exception:
                    pass


