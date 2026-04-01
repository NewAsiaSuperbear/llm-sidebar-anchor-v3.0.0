# Main entry point for LLM Scribe Pro
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
        app = MainWindow()
        app.mainloop()
    except Exception as e:
        logger.critical(f"Application crashed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
