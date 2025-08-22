from fastapi import APIRouter
from pydantic import BaseModel
import time, hashlib
router = APIRouter(prefix="/billing", tags=["billing"])
class CheckoutIn(BaseModel):
    cafe_id: int
    plan_code: str  # premium | business
@router.post("/checkout", response_model=dict)
def checkout(data: CheckoutIn):
    order_id = f"QRMENU-{int(time.time())}-{data.cafe_id}-{data.plan_code}"
    fake_url = f"https://pay.example.com/{hashlib.sha256(order_id.encode()).hexdigest()[:16]}"
    return {"order_id": order_id, "redirect_url": fake_url}
