import os
import uuid
import uvicorn

from datetime import datetime

from fastapi import FastAPI, Header
from pydantic import BaseModel

from services.observability import setup_observability
from services.faults import cpu_hog
from services.utils import verify_token_from_header

# In-memory order storage
orders_db = {}


class OrderRequest(BaseModel):
    product_id: str
    amount: float


class OrderResponse(BaseModel):
    order_id: str
    product_id: str
    amount: float
    user_id: str
    created_at: str


app = FastAPI(title="Order Service", version="1.0.0")

setup_observability(app, "order-service")

@app.post("/orders", response_model=OrderResponse)
async def create_order(
    order_req: OrderRequest,
    authorization: str = Header(None)
):
    """
    Create a new order.
    Requires valid JWT token in Authorization header.
    Format: "Bearer <token>"
    """
    # Verify token (handles all validation and Bearer parsing)
    user_id = verify_token_from_header(authorization)

    # Trigger Fault Injection - CPU Hog PF31
    if os.getenv("INJECT_CPU_HOG") == "true":
        cpu_hog()
    
    # Create order
    order_id = str(uuid.uuid4())[:8]
    order = {
        "order_id": order_id,
        "product_id": order_req.product_id,
        "amount": order_req.amount,
        "user_id": user_id,
        "created_at": datetime.utcnow().isoformat()
    }
    
    # Store in memory
    orders_db[order_id] = order
    
    return OrderResponse(**order)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)