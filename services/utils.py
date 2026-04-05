import os

from fastapi import HTTPException, status
from jose import jwt

JWT_SECRET = os.getenv("JWT_SECRET_KEY", "secret")
JWT_ALGO = "HS256"


def verify_token_from_header(authorization: str) -> str:
    """
    Extract and verify JWT token from Authorization header.
    Handles Bearer scheme parsing and token validation.
    
    Args:
        authorization: Authorization header value (e.g., "Bearer <token>")
    
    Returns:
        username from token
    
    Raises:
        HTTPException: If header missing, invalid format, or token invalid
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header"
        )
    
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization scheme"
            )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization format"
        )
    
    # Verify token
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
        username = payload.get("sub")
        
        if not username:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        return username
    
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )