import base64
import os
import subprocess
import sys

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from llm_scribe.config import ENCRYPTION_SALT

_cache = {
    "machine_id": None,
    "key": None
}

def get_machine_id():
    """Generates a semi-unique ID for the machine with caching."""
    if _cache["machine_id"]:
        return _cache["machine_id"]
    
    try:
        if sys.platform == 'win32':
            # Use PowerShell instead of wmic which might not be in PATH
            cmd = 'powershell.exe -Command "(Get-CimInstance -Class Win32_ComputerSystemProduct).UUID"'
            uuid = subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL).decode().strip()
        elif sys.platform == 'darwin':
            cmd = "ioreg -rd1 -c IOPlatformExpertDevice | grep IOPlatformUUID"
            output = subprocess.check_output(cmd, shell=True).decode()
            uuid = output.split('"')[3]
        else:
            # Linux fallback (requires root usually, so default to fallback)
            try:
                with open('/etc/machine-id') as f:
                    uuid = f.read().strip()
            except Exception:
                uuid = "default_hardware_fallback"
                
        _cache["machine_id"] = uuid.encode()
        return _cache["machine_id"]
    except Exception:
        # Fallback for non-windows or failed command
        _cache["machine_id"] = b"default_hardware_fallback"
        return _cache["machine_id"]

def generate_key():
    """Derives a stable encryption key from machine ID and external salt."""
    if _cache["key"]:
        return _cache["key"]
    
    # Use salt from config (which can be set via ENV)
    salt = ENCRYPTION_SALT.encode()
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    _cache["key"] = base64.urlsafe_b64encode(kdf.derive(get_machine_id()))
    return _cache["key"]

def encrypt_data(data_str):
    """Encrypts a string using machine-derived key."""
    try:
        f = Fernet(generate_key())
        return f.encrypt(data_str.encode()).decode()
    except Exception:
        return data_str # Fallback to plaintext if cryptography fails

def decrypt_data(encrypted_str):
    """Decrypts a string using machine-derived key."""
    try:
        f = Fernet(generate_key())
        return f.decrypt(encrypted_str.encode()).decode()
    except Exception:
        return encrypted_str # Fallback to plaintext

def sanitize_input(text):
    """Security: Strip potentially harmful characters for display/storage."""
    if not text:
        return ""
    # Remove any non-printable characters except whitespace
    return "".join(c for c in text if c.isprintable() or c in "\n\r\t")

def safe_path_check(path):
    """Security: Ensure the path is within reasonable bounds and not executable."""
    forbidden_extensions = ['.exe', '.bat', '.cmd', '.sh', '.py', '.js', '.vbs', '.msi', '.com']
    _, ext = os.path.splitext(path.lower())
    if ext in forbidden_extensions:
        return False
    return True

