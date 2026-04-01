import tkinter as tk
from tkinter import filedialog

import customtkinter as ctk

from llm_scribe.config import COLORS


class ExportDialog(ctk.CTkToplevel):
    """
    Dialog for choosing export format and destination.
    """
    def __init__(self, master, item_name, is_folder=False, on_confirm=None, **kwargs):
        super().__init__(master, **kwargs)
        self.item_name = item_name
        self.is_folder = is_folder
        self.on_confirm = on_confirm
        
        self.title(f"导出: {item_name}" if not is_folder else f"导出文件夹: {item_name}")
        self.geometry("400x300")
        self.configure(fg_color=COLORS["bg"])
        self.attributes("-topmost", True)
        self.grab_set() # Modal
        
        self.setup_ui()

    def setup_ui(self):
        # Title
        title_label = ctk.CTkLabel(
            self, text="选择导出格式 (Select Format)", 
            font=("Segoe UI", 14, "bold"), text_color=COLORS["text"]
        )
        title_label.pack(pady=(20, 10))
        
        # Format/Preset Selection
        self.format_var = tk.StringVar(value="md")
        self.preset_var = tk.StringVar(value="default")
        
        radio_frame = ctk.CTkFrame(self, fg_color="transparent")
        radio_frame.pack(pady=10)
        
        # Standard Formats
        ctk.CTkLabel(radio_frame, text="标准格式:", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        
        md_radio = ctk.CTkRadioButton(
            radio_frame, text="Markdown (.md)", 
            variable=self.format_var, value="md",
            fg_color=COLORS["accent"], border_color=COLORS["border"],
            text_color=COLORS["text"], 
            command=lambda: self.preset_var.set("default")
        )
        md_radio.pack(pady=2, anchor="w")
        
        html_radio = ctk.CTkRadioButton(
            radio_frame, text="HTML (.html)", 
            variable=self.format_var, value="html",
            fg_color=COLORS["accent"], border_color=COLORS["border"],
            text_color=COLORS["text"],
            command=lambda: self.preset_var.set("default")
        )
        html_radio.pack(pady=2, anchor="w")
        
        # Note-taking Presets
        ctk.CTkLabel(radio_frame, text="笔记软件预设:", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(10, 0))
        
        obsidian_radio = ctk.CTkRadioButton(
            radio_frame, text="Obsidian (YAML + MD)", 
            variable=self.preset_var, value="obsidian",
            fg_color=COLORS["accent"], border_color=COLORS["border"],
            text_color=COLORS["text"],
            command=lambda: self.format_var.set("md")
        )
        obsidian_radio.pack(pady=2, anchor="w")
        
        logseq_radio = ctk.CTkRadioButton(
            radio_frame, text="Logseq (Block structure)", 
            variable=self.preset_var, value="logseq",
            fg_color=COLORS["accent"], border_color=COLORS["border"],
            text_color=COLORS["text"],
            command=lambda: self.format_var.set("md")
        )
        logseq_radio.pack(pady=2, anchor="w")
        
        # Action Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(side=ctk.BOTTOM, fill=ctk.X, pady=20, padx=20)
        
        cancel_btn = ctk.CTkButton(
            btn_frame, text="取消 (Cancel)", width=100, 
            fg_color=COLORS["card"], command=self.destroy
        )
        cancel_btn.pack(side=ctk.LEFT, padx=10)
        
        confirm_btn = ctk.CTkButton(
            btn_frame, text="确认导出 (Export)", width=150, 
            fg_color=COLORS["accent"], command=self.handle_confirm
        )
        confirm_btn.pack(side=ctk.RIGHT, padx=10)

    def handle_confirm(self):
        fmt = self.format_var.get()
        preset = self.preset_var.get()
        if preset == "default":
            preset = None
        
        if self.is_folder:
            path = filedialog.askdirectory(title="选择导出目录")
        else:
            ext = f".{fmt}"
            path = filedialog.asksaveasfilename(
                title="保存导出文件",
                defaultextension=ext,
                filetypes=[
                    (f"{fmt.upper()} files", f"*{ext}"), 
                    ("All files", "*.*")
                ],
                initialfile=f"{self.item_name}{ext}"
            )
            
        if path:
            if self.on_confirm:
                self.on_confirm(fmt, path, preset)
            self.destroy()
