from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlmodel import Session, select
from ..deps import get_current_user, CurrentUser
from ..db import Cafe, Category, MenuItem, get_session
router = APIRouter(prefix="/menu", tags=["menu"])
class CategoryIn(BaseModel):
    cafe_id: int
    name: str
    sort: int = 0
@router.post("/categories", response_model=dict)
def create_category(data: CategoryIn, cu: CurrentUser = Depends(get_current_user), session: Session = Depends(get_session)):
    cafe = session.get(Cafe, data.cafe_id)
    if not cafe or cafe.owner_id != cu.user_id:
        raise HTTPException(status_code=404, detail="Cafe not found")
    cat = Category(cafe_id=cafe.id, name=data.name, sort=data.sort)
    session.add(cat); session.commit(); session.refresh(cat)
    return {"id": cat.id, "name": cat.name}
class ItemIn(BaseModel):
    cafe_id: int
    category_id: Optional[int] = None
    name: str
    price_cents: int
    description: Optional[str] = None
    sort: int = 0
@router.post("/items", response_model=dict)
def create_item(data: ItemIn, cu: CurrentUser = Depends(get_current_user), session: Session = Depends(get_session)):
    cafe = session.get(Cafe, data.cafe_id)
    if not cafe or cafe.owner_id != cu.user_id:
        raise HTTPException(status_code=404, detail="Cafe not found")
    item = MenuItem(
        cafe_id=cafe.id, category_id=data.category_id, name=data.name,
        price_cents=data.price_cents, description=data.description, sort=data.sort
    )
    session.add(item); session.commit(); session.refresh(item)
    return {"id": item.id, "name": item.name}
class ItemImageIn(BaseModel):
    image_url: str
@router.put("/items/{item_id}/image", response_model=dict)
def set_item_image(item_id: int, data: ItemImageIn, cu: CurrentUser = Depends(get_current_user), session: Session = Depends(get_session)):
    item = session.get(MenuItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    cafe = session.get(Cafe, item.cafe_id)
    if cafe.owner_id != cu.user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    item.image_url = data.image_url
    session.add(item); session.commit(); session.refresh(item)
    return {"ok": True, "image_url": item.image_url}
@router.get("/public/{slug}", response_model=dict)
def public_menu(slug: str, session: Session = Depends(get_session)):
    cafe = session.exec(select(Cafe).where(Cafe.slug == slug)).first()
    if not cafe:
        raise HTTPException(status_code=404, detail="Cafe not found")
    cats = session.exec(select(Category).where(Category.cafe_id == cafe.id).order_by(Category.sort)).all()
    items = session.exec(select(MenuItem).where(MenuItem.cafe_id == cafe.id, MenuItem.is_active == True).order_by(MenuItem.sort)).all()
    return {
        "cafe": {"name": cafe.name, "slug": cafe.slug},
        "categories": [{"id": c.id, "name": c.name, "sort": c.sort} for c in cats],
        "items": [{
            "id": i.id, "name": i.name, "price_cents": i.price_cents,
            "description": i.description, "image_url": i.image_url,
            "category_id": i.category_id
        } for i in items]
    }
