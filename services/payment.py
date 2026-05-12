import os
import uuid
import uvicorn

from datetime import datetime

from fastapi import FastAPI, Header
from pydantic import BaseModel

from services.observability import setup_observability
from services.faults import long_response_time
from services.utils import verify_token_from_header

from opentelemetry import trace

tracer = trace.get_tracer(__name__)

# In-memory payment storage
payments_db = {}


class PaymentRequest(BaseModel):
    order_id: str
    amount: float
    payment_method: str


class PaymentResponse(BaseModel):
    payment_id: str
    order_id: str
    amount: float
    payment_method: str
    status: str
    created_at: str


app = FastAPI(title="Payment Service", version="1.0.0")

setup_observability(app, "payment-service")

@app.post("/payments", response_model=PaymentResponse)
async def process_payment(
    payment_req: PaymentRequest,
    authorization: str = Header(None)
):
    """
    Process a payment.
    Requires valid JWT token in Authorization header.
    Format: "Bearer <token>"
    """
    # Verify token (handles all validation and Bearer parsing)
    user_id = verify_token_from_header(authorization)

    if os.getenv("INJECT_LONG_RESPONSE_TIME") == "true":
        with tracer.start_as_current_span("long_response_time"):
            await long_response_time()
    
    # Process payment
    payment_id = str(uuid.uuid4())[:8]
    payment = {
        "payment_id": payment_id,
        "order_id": payment_req.order_id,
        "amount": payment_req.amount,
        "payment_method": payment_req.payment_method,
        "status": "completed",
        "user_id": user_id,
        "created_at": datetime.utcnow().isoformat()
    }
    
    # Store in memory
    payments_db[payment_id] = payment
    
    return PaymentResponse(**payment)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8003)