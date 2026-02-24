from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
import hashlib
import os
import base64
from app.core.config import settings

# Use a simple PBKDF2 approach instead of bcrypt to avoid passlib issues
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password using PBKDF2-SHA256"""
    # Truncate password to 72 bytes (bcrypt limit)
    plain_password = plain_password[:72]
    
    # hashed_password format: algorithm$salt$hash
    try:
        parts = hashed_password.split('$')
        if len(parts) != 3 or parts[0] != 'pbkdf2_sha256':
            return False
        
        salt = base64.b64decode(parts[1])
        stored_hash = parts[2]
        
        # Derive key with same parameters
        derived = hashlib.pbkdf2_hmac(
            'sha256',
            plain_password.encode('utf-8'),
            salt,
            100000
        )
        derived_b64 = base64.b64encode(derived).decode('utf-8')
        
        return derived_b64 == stored_hash
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    """Hash password using PBKDF2-SHA256"""
    # Truncate password to 72 bytes (bcrypt limit)
    password = password[:72]
    
    # Generate random salt
    salt = os.urandom(32)
    salt_b64 = base64.b64encode(salt).decode('utf-8')
    
    # Derive key
    derived = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt,
        100000
    )
    derived_b64 = base64.b64encode(derived).decode('utf-8')
    
    # Return in format: algorithm$salt$hash
    return f'pbkdf2_sha256${salt_b64}${derived_b64}'


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None
