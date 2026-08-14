from base64 import urlsafe_b64encode
from hashlib import sha256

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings


class CredentialCryptoError(RuntimeError):
    pass


def _fernet() -> Fernet:
    # Derive a stable 32-byte encryption key from the application's strong JWT secret.
    # This keeps OAuth tokens encrypted at rest without introducing another operator secret.
    digest = sha256(settings.jwt_secret_key.encode("utf-8")).digest()
    return Fernet(urlsafe_b64encode(digest))


def encrypt_secret(value: str) -> str:
    if not value:
        return ""
    return _fernet().encrypt(value.encode("utf-8")).decode("ascii")


def decrypt_secret(value: str | None) -> str:
    if not value:
        return ""
    try:
        return _fernet().decrypt(value.encode("ascii")).decode("utf-8")
    except (InvalidToken, ValueError) as exc:
        raise CredentialCryptoError(
            "平台授权凭据无法解密。请重新连接该平台账号。"
        ) from exc
