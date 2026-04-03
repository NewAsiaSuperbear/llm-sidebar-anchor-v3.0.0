# Custom Styles for LLM Scribe Pro
import customtkinter as ctk
from llm_scribe.config import COLORS


class AppStyles:
    @staticmethod
    def setup_theme():
        """Initializes CustomTkinter global theme settings."""
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")  # Default CTK blue theme

    @staticmethod
    def get_fonts():
        """Returns a dictionary of font settings."""
        return {
            "main": ("Segoe UI", 12),
            "bold": ("Segoe UI", 13, "bold"),
            "title": ("Segoe UI", 16, "bold"),
            "mono": ("Consolas", 11),
            "small": ("Segoe UI", 10),
            "dim": ("Segoe UI", 10, "italic")
        }

    @staticmethod
    def apply_card_style(widget):
        """Applies a card-like appearance to a widget."""
        widget.configure(
            fg_color=COLORS["card"],
            border_color=COLORS["border"],
            border_width=1,
            corner_radius=10
        )
