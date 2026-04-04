"""
Auth Service - Minimal mock authentication for observability testing.
Generates and verifies JWT tokens. Not production-grade auth.
"""

import os
from datetime import datetime, timedelta, timezone

from fastapi import FastAPI, HTTPException
from jose import jwt
from pydantic import BaseModel


JWT_SECRET = os.getenv("JWT_SECRET_KEY", "secret")
JWT_ALGO = "HS256"
TOKEN_EXPIRE_MINS = 1440

app = FastAPI(title="Auth Service")


class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str


def create_token(username: str) -> str:
    payload = {
        "sub": username,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=TOKEN_EXPIRE_MINS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGO)


def verify_token(token: str) -> str:
    """Verify token and return username"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
        return payload.get("sub")
    except:
        raise HTTPException(status_code=401, detail="Invalid token")


@app.post("/auth/login", response_model=TokenResponse)
async def login(creds: LoginRequest):
    """Login with any username/password - returns a token"""
    # Mock: accept any credentials
    token = create_token(creds.username)
    return TokenResponse(access_token=token, token_type="bearer")


@app.post("/auth/verify")
async def verify(token: str):
    """Verify a token"""
    username = verify_token(token)
    return {"username": username}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)