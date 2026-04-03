import os
import re
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Optional


def get_machine_id_bytes() -> bytes:
    value = _get_platform_machine_id()
    if value:
        return value.encode()
    return _get_or_create_persisted_id().encode()


def _get_platform_machine_id() -> Optional[str]:
    if sys.platform == "win32":
        return _get_machine_id_windows()
    if sys.platform == "darwin":
        return _get_machine_id_macos()
    return _get_machine_id_linux()


def _get_machine_id_linux() -> Optional[str]:
    for path in ("/etc/machine-id", "/var/lib/dbus/machine-id"):
        try:
            p = Path(path)
            if p.exists():
                value = p.read_text(encoding="utf-8", errors="ignore").strip()
                if value:
                    return value
        except Exception:
            continue
    return None


def _get_machine_id_macos() -> Optional[str]:
    try:
        proc = subprocess.run(
            ["ioreg", "-rd1", "-c", "IOPlatformExpertDevice"],
            check=False,
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0:
            return None
        m = re.search(r'"IOPlatformUUID"\s*=\s*"([^"]+)"', proc.stdout)
        return m.group(1).strip() if m else None
    except Exception:
        return None


def _get_machine_id_windows() -> Optional[str]:
    try:
        proc = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                "(Get-CimInstance Win32_ComputerSystemProduct).UUID",
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        value = (proc.stdout or "").strip()
        if proc.returncode == 0 and value and value.upper() != "FFFFFFFF-FFFF-FFFF-FFFF-FFFFFFFFFFFF":
            return value
    except Exception:
        pass

    try:
        node = uuid.getnode()
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"llm-scribe-pro:win-node:{node}"))
    except Exception:
        return None


def _get_or_create_persisted_id() -> str:
    path = _persisted_id_path()
    try:
        if path.exists():
            value = path.read_text(encoding="utf-8", errors="ignore").strip()
            if value:
                return value
    except Exception:
        pass

    value = str(uuid.uuid4())
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value, encoding="utf-8")
    except Exception:
        pass
    return value


def _persisted_id_path() -> Path:
    from llm_scribe.config import get_app_data_dir

    base = os.getenv("LLM_SCRIBE_DATA_DIR")
    if base:
        return Path(base).expanduser().resolve() / "machine_id"
    return get_app_data_dir() / "machine_id"
