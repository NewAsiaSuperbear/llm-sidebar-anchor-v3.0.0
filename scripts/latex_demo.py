import os
import subprocess
import sys
import argparse
from pathlib import Path


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _venv_python(venv_dir: Path) -> Path:
    if os.name == "nt":
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def _pip_available(python_exe: Path, *, cwd: Path) -> bool:
    try:
        subprocess.check_call([str(python_exe), "-m", "pip", "--version"], cwd=str(cwd), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception:
        return False


def _ensure_venv_and_deps(project_root: Path, *, force: bool = False) -> Path:
    venv_dir = project_root / ".venv"
    python_exe = _venv_python(venv_dir)

    if force or not python_exe.exists():
        subprocess.check_call([sys.executable, "-m", "venv", str(venv_dir)], cwd=str(project_root))

    if not _pip_available(python_exe, cwd=project_root):
        try:
            subprocess.check_call([str(python_exe), "-m", "ensurepip", "--upgrade"], cwd=str(project_root), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            python_exe = Path(sys.executable).resolve()

    check_code = "import customtkinter,cryptography,pystray,pynput,PIL,dotenv,requests,jinja2,markdown,pygments,matplotlib"
    try:
        subprocess.check_call([str(python_exe), "-c", check_code], cwd=str(project_root))
    except Exception:
        if not _pip_available(python_exe, cwd=project_root):
            raise
        subprocess.check_call([str(python_exe), "-m", "pip", "install", "--upgrade", "pip"], cwd=str(project_root))
        subprocess.check_call([str(python_exe), "-m", "pip", "install", "-e", "."], cwd=str(project_root))

    return python_exe


def _ensure_import_paths(project_root: Path) -> None:
    src_path = str(project_root / "src")
    if src_path not in sys.path:
        sys.path.insert(0, src_path)


def _configure_dev_env(project_root: Path) -> None:
    dev_data_dir = project_root / ".devdata"
    os.environ.setdefault("LLM_SCRIBE_DATA_DIR", str(dev_data_dir))
    os.environ.setdefault("LLM_SCRIBE_SALT", "dev_demo_salt_change_me")


def main() -> None:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--run", action="store_true")
    args = parser.parse_args()

    project_root = _project_root()
    venv_python = _ensure_venv_and_deps(project_root)

    if not args.run and Path(sys.executable).resolve() != venv_python.resolve():
        cmd = [str(venv_python), str(Path(__file__).resolve()), "--run"]
        raise SystemExit(subprocess.call(cmd, cwd=str(project_root)))

    _configure_dev_env(project_root)
    _ensure_import_paths(project_root)

    from llm_scribe.ui.main_window import MainWindow

    app = MainWindow()

    def seed_demo() -> None:
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


if __name__ == "__main__":
    main()
