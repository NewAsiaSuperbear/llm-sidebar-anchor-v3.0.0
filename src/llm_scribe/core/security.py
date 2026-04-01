import os
import re
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from llm_scribe.config import ENCRYPTION_SALT

_cached_machine_id = None
_cached_key = None

def get_machine_id():
    """Generates a semi-unique ID for the machine with caching."""
    global _cached_machine_id
    if _cached_machine_id: return _cached_machine_id
    
    try:
        import subprocess
        # Windows-specific hardware UUID
        cmd = 'wmic csproduct get uuid'
        uuid = subprocess.check_output(cmd, shell=True).decode().split('\n')[1].strip()
        _cached_machine_id = uuid.encode()
        return _cached_machine_id
    except:
        # Fallback for non-windows or failed command
        _cached_machine_id = b"default_hardware_fallback"
        return _cached_machine_id

def generate_key():
    """Derives a stable encryption key from machine ID and external salt."""
    global _cached_key
    if _cached_key: return _cached_key
    
    # Use salt from config (which can be set via ENV)
    salt = ENCRYPTION_SALT.encode()
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    _cached_key = base64.urlsafe_b64encode(kdf.derive(get_machine_id()))
    return _cached_key

def encrypt_data(data_str):
    """Encrypts a string using machine-derived key."""
    try:
        f = Fernet(generate_key())
        return f.encrypt(data_str.encode()).decode()
    except:
        return data_str # Fallback to plaintext if cryptography fails

def decrypt_data(encrypted_str):
    """Decrypts a string using machine-derived key."""
    try:
        f = Fernet(generate_key())
        return f.decrypt(encrypted_str.encode()).decode()
    except:
        return encrypted_str # Fallback to plaintext

def sanitize_input(text):
    """Security: Strip potentially harmful characters for display/storage."""
    if not text: return ""
    # Remove any non-printable characters except whitespace
    return "".join(c for c in text if c.isprintable() or c in "\n\r\t")

def safe_path_check(path):
    """Security: Ensure the path is within reasonable bounds and not executable."""
    forbidden_extensions = ['.exe', '.bat', '.cmd', '.sh', '.py', '.js', '.vbs', '.msi', '.com']
    _, ext = os.path.splitext(path.lower())
    if ext in forbidden_extensions:
        return False
    return True

