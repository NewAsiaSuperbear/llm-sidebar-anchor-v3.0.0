# Main entry point for LLM Scribe Pro
import argparse
import sys
from pathlib import Path

from llm_scribe.config import VERSION
from llm_scribe.ui.main_window import MainWindow
from llm_scribe.utils.logger import logger

# Add src to sys.path if running directly
src_path = str(Path(__file__).parent.parent)
if src_path not in sys.path:
    sys.path.append(src_path)


def main():
    """Starts the LLM Scribe Pro application."""
    logger.info(f"Starting LLM Scribe Pro v{VERSION} (Modernized)...")
    try:
        parser = argparse.ArgumentParser(add_help=True)
        parser.add_argument("--latex-demo", action="store_true")
        args = parser.parse_args()

        app = MainWindow()
        if args.latex_demo:
            def seed_demo():
                app.create_new_session("LaTeX Demo")
                sample = "\n".join(
                    [
                        "Inline: $E=mc^2$, $\\frac{a}{b}$, $\\sum_{i=1}^n i$",
                        "",
                        "Display:",
                        "$$\\int_0^1 x^2\\,dx = \\frac{1}{3}$$",
                        "",
                        "Bracket display:",
                        "\\[ \\nabla \\cdot \\mathbf{E} = \\frac{\\rho}{\\varepsilon_0} \\]",
                        "",
                        "Paren inline: \\(\\alpha+\\beta=\\gamma\\)",
                    ]
                )
                app._set_raw_content(sample)
                app._render_view_from_raw()
                app.save_current_session()

            app.after(50, seed_demo)
        app.mainloop()
    except Exception as e:
        logger.critical(f"Application crashed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
