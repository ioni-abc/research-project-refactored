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

@app.post("/auth/login", response_model=TokenResponse)
async def login(creds: LoginRequest):
    """Login with any username/password - returns a token"""
    # Mock: accept any credentials
    token = create_token(creds.username)
    return TokenResponse(access_token=token, token_type="bearer")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)