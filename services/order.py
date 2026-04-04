"""
Order Service - Handles order placement
Requires JWT token from Auth Service
"""

from fastapi import FastAPI, Depends
from pydantic import BaseModel
from datetime import datetime
import uuid
from utils import verify_token, security

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


app = FastAPI(title="Order Service")


@app.post("/orders", response_model=OrderResponse)
async def create_order(
    order_req: OrderRequest,
    credentials = Depends(security)
):
    """
    Create a new order.
    Requires valid JWT token in Authorization header.
    """
    # Verify token
    user_id = verify_token(credentials)
    
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
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)