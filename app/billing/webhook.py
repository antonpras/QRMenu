from fastapi import APIRouter, Request, HTTPException, Depends
from sqlmodel import Session, select
from datetime import datetime, timedelta
from ..db import Subscription, Cafe, get_session
router = APIRouter(prefix="/billing/webhook", tags=["billing"])
@router.post("/midtrans")
async def midtrans_webhook(request: Request, session: Session = Depends(get_session)):
    payload = await request.json()
    order_id = payload.get("order_id")
    transaction_status = payload.get("transaction_status")
    cafe_id = payload.get("cafe_id")
    plan_code = payload.get("plan_code", "premium")
    if not (order_id and transaction_status and cafe_id):
        raise HTTPException(status_code=400, detail="invalid payload")
    cafe = session.get(Cafe, cafe_id)
    if not cafe:
        raise HTTPException(status_code=404, detail="cafe not found")
    sub = session.exec(select(Subscription).where(Subscription.cafe_id == cafe.id)).first()
    if not sub:
        sub = Subscription(cafe_id=cafe.id, plan_code="free", status="active")
        session.add(sub); session.commit(); session.refresh(sub)
    if transaction_status in {"settlement", "capture"}:
        sub.plan_code = plan_code
        sub.status = "active"
        sub.started_at = datetime.utcnow()
        sub.expires_at = datetime.utcnow() + timedelta(days=30)
        sub.payment_ref = order_id
        session.add(sub); session.commit(); session.refresh(sub)
    return {"ok": True}
