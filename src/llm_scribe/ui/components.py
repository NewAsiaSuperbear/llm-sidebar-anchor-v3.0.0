import customtkinter as ctk

from llm_scribe.config import COLORS
from llm_scribe.ui.styles import AppStyles


class Toast(ctk.CTkFrame):
    def __init__(self, master, message, duration=2000, **kwargs):
        super().__init__(master, **kwargs)
        self.message = message
        self.duration = duration
        self.fonts = AppStyles.get_fonts()
        self.setup_ui()

    def setup_ui(self):
        """Initializes the Toast appearance and animation."""
        self.configure(
            fg_color=COLORS["accent"],
            corner_radius=20,
            border_width=0
        )
        self.label = ctk.CTkLabel(
            self, text=self.message, 
            font=self.fonts["bold"], 
            text_color="white"
        )
        self.label.pack(padx=20, pady=10)

    def show(self):
        """Displays the toast and schedules its removal."""
        self.place(relx=0.5, rely=0.1, anchor="n")
        self.after(self.duration, self.destroy)

class EmptyState(ctk.CTkFrame):
    def __init__(self, master, message="点击 '+新建' 开始第一个笔记", **kwargs):
        super().__init__(master, **kwargs)
        self.message = message
        self.fonts = AppStyles.get_fonts()
        self.setup_ui()

    def setup_ui(self):
        """Initializes the Empty State UI components."""
        self.configure(fg_color="transparent")
        self.icon_label = ctk.CTkLabel(
            self, text="📚", font=("Segoe UI Emoji", 48)
        )
        self.icon_label.pack(pady=(20, 10))
        self.text_label = ctk.CTkLabel(
            self, text=self.message, font=self.fonts["bold"], 
            text_color=COLORS["text_dim"]
        )
        self.text_label.pack()

class StatusIndicator(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.setup_ui()

    def setup_ui(self):
        """Initializes a simple colored indicator dot."""
        self.configure(width=10, height=10, corner_radius=5)
        self.set_status(False)

    def set_status(self, active):
        """Updates the indicator color based on activity."""
        color = COLORS["success"] if active else COLORS["danger"]
        self.configure(fg_color=color)
