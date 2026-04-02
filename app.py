import hashlib
import os
import subprocess
import sys
from pathlib import Path

try:
    import tkinter as tk
    from tkinter import messagebox
except Exception:
    tk = None
    messagebox = None


def _notify(title: str, message: str, *, is_error: bool = False) -> None:
    try:
        if tk is not None and messagebox is not None:
            root = tk.Tk()
            root.withdraw()
            try:
                root.attributes("-topmost", True)
            except Exception:
                pass
            if is_error:
                messagebox.showerror(title, message)
            else:
                messagebox.showinfo(title, message)
            root.destroy()
            return
    except Exception:
        pass

    stream = sys.stderr if is_error else sys.stdout
    try:
        stream.write(f"{title}: {message}\n")
    except Exception:
        pass


def _venv_python(venv_dir: Path) -> Path:
    if os.name == "nt":
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def _run(cmd: list[str], *, cwd: Path) -> None:
    subprocess.check_call(cmd, cwd=str(cwd))


def _has_deps(python_exe: Path) -> bool:
    check_code = "import customtkinter,cryptography,pystray,pynput,PIL,dotenv,requests,jinja2,markdown,pygments"
    try:
        subprocess.check_call(
            [str(python_exe), "-c", check_code],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True
    except Exception:
        return False


def _fallback_venv_dir(project_root: Path) -> Path:
    env_id = hashlib.sha1(str(project_root).encode("utf-8")).hexdigest()[:10]
    override = os.environ.get("LLM_SCRIBE_VENV_DIR")
    if override:
        return Path(override).expanduser().resolve()

    if os.name == "nt":
        base = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "LLMScribePro" / "venvs"
    else:
        base = Path(os.environ.get("XDG_STATE_HOME", str(Path.home() / ".local" / "state"))) / "llm_scribe_pro" / "venvs"
    base.mkdir(parents=True, exist_ok=True)
    return base / f"llm_scribe_pro_{env_id}"


def main() -> None:
    project_root = Path(__file__).resolve().parent

    venv_dir = project_root / ".venv"
    python_exe = _venv_python(venv_dir)

    try:
        if not python_exe.exists():
            try:
                _notify("LLM Scribe Pro", f"首次运行将创建虚拟环境并安装依赖，请稍候。\n\n虚拟环境位置：\n{venv_dir}")
                _run([sys.executable, "-m", "venv", str(venv_dir)], cwd=project_root)
            except Exception:
                venv_dir = _fallback_venv_dir(project_root)
                python_exe = _venv_python(venv_dir)
                _notify("LLM Scribe Pro", f"当前目录不可写或创建失败，将改用备用位置。\n\n虚拟环境位置：\n{venv_dir}")
                _run([sys.executable, "-m", "venv", str(venv_dir)], cwd=project_root)

        if not _has_deps(python_exe):
            _notify("LLM Scribe Pro", "正在安装/更新依赖，请稍候。")
            _run([str(python_exe), "-m", "pip", "install", "--upgrade", "pip"], cwd=project_root)
            _run([str(python_exe), "-m", "pip", "install", "-e", "."], cwd=project_root)

        subprocess.call([str(python_exe), "-m", "llm_scribe.main"], cwd=str(project_root))
    except Exception as e:
        _notify("LLM Scribe Pro 启动失败", f"{type(e).__name__}: {e}", is_error=True)
        raise SystemExit(1) from e

if __name__ == "__main__":
    main()
