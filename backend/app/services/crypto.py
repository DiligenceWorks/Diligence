"""Fernet encryption for integration credentials.

Derives a Fernet-compatible key from the app SECRET_KEY using HKDF.
The SECRET_KEY can be any format (hex string, random bytes, passphrase).
"""
from __future__ import annotations

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
import base64

_fernet_instance: Fernet | None = None


def _derive_fernet_key(secret_key: str) -> bytes:
    """Derive a Fernet-compatible key from the app SECRET_KEY."""
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b"diligence-integration-encryption",
        info=b"fernet-key",
    )
    raw = hkdf.derive(secret_key.encode())
    return base64.urlsafe_b64encode(raw)


def get_fernet(secret_key: str) -> Fernet:
    global _fernet_instance
    if _fernet_instance is None:
        _fernet_instance = Fernet(_derive_fernet_key(secret_key))
    return _fernet_instance


def encrypt_value(secret_key: str, plaintext: str) -> str:
    """Encrypt a plaintext string. Returns base64-encoded ciphertext."""
    return get_fernet(secret_key).encrypt(plaintext.encode()).decode()


def decrypt_value(secret_key: str, ciphertext: str) -> str:
    """Decrypt a ciphertext string. Returns plaintext."""
    return get_fernet(secret_key).decrypt(ciphertext.encode()).decode()
