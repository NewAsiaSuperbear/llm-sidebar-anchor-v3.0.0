import customtkinter as ctk

from llm_scribe.config import COLORS
from llm_scribe.ui.styles import AppStyles


class FirstRunWizard(ctk.CTkToplevel):
    def __init__(self, master, on_complete_callback, **kwargs):
        super().__init__(master, **kwargs)
        self.on_complete = on_complete_callback
        self.fonts = AppStyles.get_fonts()
        self.step = 1
        self.setup_ui()
        self.update_step()

    def setup_ui(self):
        """Initializes the wizard layout."""
        self.title("首次运行向导 (First-Run Guide)")
        self.geometry("500x400")
        self.configure(fg_color=COLORS["bg"])
        self.attributes("-topmost", True)
        self.grab_set()

        # Step content container
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.pack(fill=ctk.BOTH, expand=True, padx=30, pady=30)

        self.title_label = ctk.CTkLabel(
            self.content_frame, text="", font=self.fonts["title"]
        )
        self.title_label.pack(pady=(0, 20))

        self.desc_label = ctk.CTkLabel(
            self.content_frame, text="", font=self.fonts["main"], 
            wraplength=400, justify="left"
        )
        self.desc_label.pack(pady=10)

        # Navigation buttons
        self.nav_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.nav_frame.pack(side=ctk.BOTTOM, fill=ctk.X, pady=20)

        self.prev_btn = ctk.CTkButton(
            self.nav_frame, text="上一步 (Prev)", width=100, command=self.prev_step
        )
        self.prev_btn.pack(side=ctk.LEFT, padx=20)

        self.next_btn = ctk.CTkButton(
            self.nav_frame, text="下一步 (Next)", width=100, command=self.next_step
        )
        self.next_btn.pack(side=ctk.RIGHT, padx=20)

    def update_step(self):
        """Updates the content based on the current step."""
        if self.step == 1:
            self.title_label.configure(text="欢迎使用 (Welcome!)")
            desc = (
                "LLM Scribe Pro 是您的 AI 对话速记员。\n\n"
                "它会自动监控剪贴板, 并将您的对话内容同步整理到不同的会话中。"
            )
            self.desc_label.configure(text=desc)
            self.prev_btn.configure(state="disabled")
        elif self.step == 2:
            self.title_label.configure(text="速记模式 (Scribe Mode)")
            desc = (
                "点击顶部的 '🚀 速记 (Scribe)' 按钮即可开启。\n\n"
                "开启后, 您在浏览器或客户端中复制的内容将自动被捕获。"
            )
            self.desc_label.configure(text=desc)
            self.prev_btn.configure(state="normal")
        elif self.step == 3:
            self.title_label.configure(text="会话与文件夹 (Structure)")
            desc = (
                "📄 '会话' 就像一本笔记本, 记录单次对话。\n"
                "📁 '文件夹' 就像书架, 帮您分类管理不同的项目。"
            )
            self.desc_label.configure(text=desc)
            self.next_btn.configure(text="完成 (Finish)")
        else:
            self.on_complete()
            self.destroy()

    def next_step(self):
        self.step += 1
        self.update_step()

    def prev_step(self):
        if self.step > 1:
            self.step -= 1
            self.update_step()
            self.next_btn.configure(text="下一步 (Next)")
