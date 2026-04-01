import customtkinter as ctk
import tkinter as tk
from llm_scribe.config import COLORS

class MoveDialog(ctk.CTkToplevel):
    """
    Dialog for moving a session to a folder.
    """
    def __init__(self, master, item_name, folders, on_confirm=None, **kwargs):
        super().__init__(master, **kwargs)
        self.item_name = item_name
        self.folders = folders
        self.on_confirm = on_confirm
        
        self.title(f"移动会话: {item_name}")
        self.geometry("400x400")
        self.configure(fg_color=COLORS["bg"])
        self.attributes("-topmost", True)
        self.grab_set() # Modal
        
        self.setup_ui()

    def setup_ui(self):
        # Title
        title_label = ctk.CTkLabel(
            self, text="选择目标文件夹 (Select Folder)", 
            font=("Segoe UI", 14, "bold"), text_color=COLORS["text"]
        )
        title_label.pack(pady=(20, 10))
        
        # Scrollable List for Folders
        self.folder_var = tk.StringVar(value="")
        
        scroll_frame = ctk.CTkScrollableFrame(self, fg_color=COLORS["sidebar"])
        scroll_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Option for "Root" (no folder)
        root_radio = ctk.CTkRadioButton(
            scroll_frame, text="📄 根目录 (No Folder)", 
            variable=self.folder_var, value="",
            fg_color=COLORS["accent"], border_color=COLORS["border"]
        )
        root_radio.pack(pady=5, anchor="w")
        
        # All available folders
        for folder in self.folders:
            f_radio = ctk.CTkRadioButton(
                scroll_frame, text=f"📁 {folder['name']}", 
                variable=self.folder_var, value=folder['id'],
                fg_color=COLORS["accent"], border_color=COLORS["border"]
            )
            f_radio.pack(pady=5, anchor="w")
            
        # Action Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(side=ctk.BOTTOM, fill=ctk.X, pady=20, padx=20)
        
        cancel_btn = ctk.CTkButton(
            btn_frame, text="取消 (Cancel)", width=100, 
            fg_color=COLORS["card"], command=self.destroy
        )
        cancel_btn.pack(side=ctk.LEFT, padx=10)
        
        confirm_btn = ctk.CTkButton(
            btn_frame, text="确认移动 (Move)", width=150, 
            fg_color=COLORS["accent"], command=self.handle_confirm
        )
        confirm_btn.pack(side=ctk.RIGHT, padx=10)

    def handle_confirm(self):
        target_folder_id = self.folder_var.get()
        if self.on_confirm:
            self.on_confirm(target_folder_id)
        self.destroy()
