from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select
from ..db import get_session, Cafe, Category, MenuItem

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/m/{slug}", response_class=HTMLResponse, tags=["public"])
def menu_landing(slug: str, request: Request, session: Session = Depends(get_session)):
    cafe = session.exec(select(Cafe).where(Cafe.slug == slug)).first()
    if not cafe:
        raise HTTPException(status_code=404, detail="Cafe not found")

    cats = session.exec(
        select(Category).where(Category.cafe_id == cafe.id).order_by(Category.sort)
    ).all()
    items = session.exec(
        select(MenuItem)
        .where(MenuItem.cafe_id == cafe.id, MenuItem.is_active == True)
        .order_by(MenuItem.sort)
    ).all()

    # Susun items per kategori (untuk tab)
    items_by_cat: dict[int | None, list[MenuItem]] = {}
    for it in items:
        items_by_cat.setdefault(it.category_id, []).append(it)

    return templates.TemplateResponse(
        "menu.html",
        {
            "request": request,
            "cafe": cafe,
            "categories": cats,
            "items": items,
            "items_by_cat": items_by_cat,
        },
    )
    
