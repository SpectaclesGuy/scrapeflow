from __future__ import annotations

import hashlib
import hmac
import secrets
from base64 import urlsafe_b64decode, urlsafe_b64encode

SCRYPT_N = 2**14
SCRYPT_R = 8
SCRYPT_P = 1
SCRYPT_DKLEN = 64


def _encode(value: bytes) -> str:
    return urlsafe_b64encode(value).decode('utf-8')


def _decode(value: str) -> bytes:
    return urlsafe_b64decode(value.encode('utf-8'))


def hash_password(password: str) -> str:
    if len(password) < 8:
        raise ValueError('Password must be at least 8 characters.')
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(
        password.encode('utf-8'),
        salt=salt,
        n=SCRYPT_N,
        r=SCRYPT_R,
        p=SCRYPT_P,
        dklen=SCRYPT_DKLEN,
    )
    return f'scrypt${SCRYPT_N}${SCRYPT_R}${SCRYPT_P}${_encode(salt)}${_encode(digest)}'


def verify_password(password: str, stored_hash: str | None) -> bool:
    if not stored_hash:
        return False
    try:
        algorithm, n, r, p, salt, expected = stored_hash.split('$', 5)
    except ValueError:
        return False
    if algorithm != 'scrypt':
        return False
    digest = hashlib.scrypt(
        password.encode('utf-8'),
        salt=_decode(salt),
        n=int(n),
        r=int(r),
        p=int(p),
        dklen=SCRYPT_DKLEN,
    )
    return hmac.compare_digest(_encode(digest), expected)
