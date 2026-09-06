"""
JWT Authentication utilities for Gatimaan prototype.
Simplified role-based auth using JWT tokens.
"""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import settings

# Use PLAINTEXT scheme for demo prototype (not for production!)
# For production, use Supabase Auth or proper password hashing
pwd_context = CryptContext(schemes=["plaintext"], deprecated="auto")
security = HTTPBearer(auto_error=False)

# Prototype demo users (in production, use Supabase Auth)
# Using plaintext passwords for prototype - NOT RECOMMENDED FOR PRODUCTION
DEMO_USERS = {
    "admin": {
        "username": "admin",
        "password": "admin123",
        "role": "Admin",
        "name": "System Administrator",
        "department": "All",
    },
    "control": {
        "username": "control",
        "password": "control123",
        "role": "Control Office",
        "name": "Control Office Officer",
        "department": "Control Office",
    },
    "engineer": {
        "username": "engineer",
        "password": "eng123",
        "role": "Engineering",
        "name": "Senior Engineer",
        "department": "Engineering",
    },
    "signal": {
        "username": "signal",
        "password": "signal123",
        "role": "S&T",
        "name": "S&T Inspector",
        "department": "S&T",
    },
    "traction": {
        "username": "traction",
        "password": "traction123",
        "role": "Traction Distribution",
        "name": "TRD Inspector",
        "department": "Traction Distribution",
    },
    "demo": {
        "username": "demo",
        "password": "demo",
        "role": "Admin",
        "name": "Demo User",
        "department": "All",
    },
}


def verify_password(plain_password: str, stored_password: str) -> bool:
    # For prototype, use simple string comparison
    # In production, use: return pwd_context.verify(plain_password, hashed_password)
    return plain_password == stored_password


def authenticate_user(username: str, password: str) -> Optional[dict]:
    user = DEMO_USERS.get(username)
    if not user:
        return None
    if not verify_password(password, user["password"]):
        return None
    return user


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> dict:
    """Extract and validate JWT token. Returns user info or demo user for prototype."""
    if credentials is None:
        # Allow demo access without auth in prototype mode
        if settings.PROTOTYPE_MODE:
            return DEMO_USERS["demo"]
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
        username = payload.get("sub")
        if username is None or username not in DEMO_USERS:
            raise HTTPException(status_code=401, detail="Invalid token")
        return DEMO_USERS[username]
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
