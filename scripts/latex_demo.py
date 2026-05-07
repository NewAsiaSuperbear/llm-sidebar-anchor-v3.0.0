import os
import subprocess
import sys
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


def _configure_dev_env(project_root: Path) -> None:
    dev_data_dir = project_root / ".devdata"
    os.environ.setdefault("LLM_SCRIBE_DATA_DIR", str(dev_data_dir))
    os.environ.setdefault("LLM_SCRIBE_SALT", "dev_demo_salt_change_me")


def main() -> None:
    project_root = _project_root()
    venv_python = _ensure_venv_and_deps(project_root)

    _configure_dev_env(project_root)
    env = os.environ.copy()
    env["LLM_SCRIBE_DATA_DIR"] = os.environ["LLM_SCRIBE_DATA_DIR"]
    env["LLM_SCRIBE_SALT"] = os.environ["LLM_SCRIBE_SALT"]
    raise SystemExit(subprocess.call([str(venv_python), "-m", "llm_scribe.main", "--latex-demo"], cwd=str(project_root), env=env))


if __name__ == "__main__":
    main()
