import os
import sys
from pathlib import Path

# Add src to sys.path
sys.path.append(str(Path(__file__).parent.parent / "src"))

# Mock environment variable for testing
os.environ["LLM_SCRIBE_SALT"] = "test_salt_12345"

from llm_scribe.core.security import generate_key, encrypt_content, decrypt_content

def test_encryption_cycle():
    """Verifies that content can be encrypted and decrypted with the current salt."""
    original_text = "This is a secret message for GitHub testing."
    
    # Encrypt
    encrypted = encrypt_content(original_text)
    assert encrypted != original_text
    
    # Decrypt
    decrypted = decrypt_content(encrypted)
    assert decrypted == original_text
    print("Encryption cycle test PASSED.")

if __name__ == "__main__":
    test_encryption_cycle()
