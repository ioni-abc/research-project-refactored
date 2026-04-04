from fastapi import HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt
import os

JWT_SECRET = os.getenv("JWT_SECRET_KEY", "secret")
JWT_ALGO = "HS256"

security = HTTPBearer()


def verify_token(credentials: HTTPAuthorizationCredentials) -> str:
    """
    Verify JWT token from Authorization header.
    Used with FastAPI's Depends() for automatic header handling.
    
    Args:
        credentials: HTTPAuthenticationCredentials from FastAPI's HTTPBearer
    
    Returns:
        username from token
    
    Raises:
        HTTPException: If token is invalid or expired
    """
    token = credentials.credentials
    
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