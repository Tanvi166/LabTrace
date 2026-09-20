import jwt
import hashlib
import bcrypt
from datetime import datetime, timedelta, timezone
from typing import Optional
from app.core.config import settings

def _hash_raw_password(password: str) -> bytes:
    # Hash raw password with SHA-256 first to avoid 72-byte bcrypt limit and passlib bug
    sha256 = hashlib.sha256(password.encode('utf-8')).hexdigest()
    return sha256.encode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        raw = _hash_raw_password(plain_password)
        return bcrypt.checkpw(raw, hashed_password.encode('utf-8'))
    except Exception:
        return False

def get_password_hash(password: str) -> str:
    raw = _hash_raw_password(password)
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(raw, salt)
    return hashed.decode('utf-8')

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None
