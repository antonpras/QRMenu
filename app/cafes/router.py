from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select
from ..deps import get_current_user, CurrentUser
from ..db import Cafe, Subscription, get_session
from ..utils import slugify
router = APIRouter(prefix="/cafes", tags=["cafes"])
class CafeIn(BaseModel):
    name: str
@router.post("", response_model=dict)
def create_cafe(data: CafeIn, cu: CurrentUser = Depends(get_current_user), session: Session = Depends(get_session)):
    slug = slugify(data.name)
    exists = session.exec(select(Cafe).where(Cafe.slug == slug)).first()
    if exists:
        slug = f"{slug}-{exists.id or 'x'}"
    cafe = Cafe(owner_id=cu.user_id, name=data.name, slug=slug)
    session.add(cafe); session.commit(); session.refresh(cafe)
    sub = Subscription(cafe_id=cafe.id, plan_code="free", status="active")
    session.add(sub); session.commit()
    return {"id": cafe.id, "slug": cafe.slug, "plan": sub.plan_code}
@router.get("/me", response_model=dict)
def my_cafes(cu: CurrentUser = Depends(get_current_user), session: Session = Depends(get_session)):
    cafes = session.exec(select(Cafe).where(Cafe.owner_id == cu.user_id)).all()
    out = []
    for c in cafes:
        sub = session.exec(select(Subscription).where(Subscription.cafe_id == c.id)).first()
        out.append({"id": c.id, "name": c.name, "slug": c.slug, "plan": sub.plan_code if sub else "free"})
    return {"cafes": out}
