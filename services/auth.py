import os
import uvicorn

from datetime import datetime, timedelta, timezone

from fastapi import FastAPI, HTTPException
from jose import jwt
from pydantic import BaseModel

from services.observability import setup_observability
from services.faults import service_unavailable

from opentelemetry import trace

tracer = trace.get_tracer(__name__)

JWT_SECRET = os.getenv("JWT_SECRET_KEY")
JWT_ALGO = os.getenv("JWT_ALGO")
JWT_EXPIRATION_MINUTES = os.getenv("JWT_EXPIRATION_MINUTES")



class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str

app = FastAPI(title="Auth Service")

setup_observability(app, "auth-service")

def create_token(username: str) -> str:
    payload = {
        "sub": username,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=int(JWT_EXPIRATION_MINUTES))
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGO)


@app.post("/auth/login", response_model=TokenResponse)
async def login(creds: LoginRequest):
    """Login with any username/password - returns a token"""

    # Trigger Fault Injection - Service Unavailable RF12
    if os.getenv("INJECT_SERVICE_UNAVAILABLE") == "true":
        with tracer.start_as_current_span("service_unavailable"):
            service_unavailable()

    # Mock: accept any credentials
    token = create_token(creds.username)
    return TokenResponse(access_token=token, token_type="bearer")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)