from fastapi import APIRouter, Request, Depends, Form, HTTPException, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select
from ..db import get_session
from ..owner.deps import get_current_user_from_cookie
from ..cafes.models import Cafe
from ..menu.models import Category, MenuItem
from ..media.router import presign_upload  # fungsi presign yang sudah ada
import os, httpx

templates = Jinja2Templates(directory="templates")

router = APIRouter(prefix="/owner", tags=["owner"])

# ---------- Auth views ----------
@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("owner/login.html", {"request": request})

@router.post("/login")
def login_action(email: str = Form(...), password: str = Form(...)):
    # call existing /auth/login
    with httpx.Client(timeout=10, follow_redirects=True) as c:
        r = c.post("/auth/login", json={"email": email, "password": password})
        if r.status_code >= 400:
            raise HTTPException(401, "Email/password salah")
        token = r.json().get("access_token")
    resp = RedirectResponse("/owner", status_code=302)
    resp.set_cookie("session", token, httponly=True, secure=True, samesite="lax", max_age=7*24*3600)
    return resp

@router.get("/logout")
def logout():
    resp = RedirectResponse("/owner/login", status_code=302)
    resp.delete_cookie("session")
    return resp

# ---------- Pages ----------
@router.get("", response_class=HTMLResponse)
def dashboard(request: Request, user=Depends(get_current_user_from_cookie), db: Session = Depends(get_session)):
    cafes = db.exec(select(Cafe).where(Cafe.owner_id == user.id).order_by(Cafe.id.desc())).all()
    return templates.TemplateResponse("owner/dashboard.html", {"request": request, "user": user, "cafes": cafes})

@router.post("/cafes/create")
def create_cafe(
    name: str = Form(...),
    slug: str | None = Form(None),
    brand_color: str | None = Form(None),
    wa_phone: str | None = Form(None),
    user=Depends(get_current_user_from_cookie),
    db: Session = Depends(get_session),
):
    cafe = Cafe(name=name, slug=slug, brand_color=brand_color, wa_phone=wa_phone, owner_id=user.id)
    db.add(cafe); db.commit(); db.refresh(cafe)
    return RedirectResponse("/owner", status_code=302)

@router.get("/cafes/{cafe_id}", response_class=HTMLResponse)
def cafe_page(
    cafe_id: int, request: Request,
    user=Depends(get_current_user_from_cookie),
    db: Session = Depends(get_session),
):
    cafe = db.get(Cafe, cafe_id)
    if not cafe or cafe.owner_id != user.id: raise HTTPException(404)
    cats = db.exec(select(Category).where(Category.cafe_id == cafe.id).order_by(Category.sort)).all()
    items = db.exec(select(MenuItem).where(MenuItem.cafe_id == cafe.id).order_by(MenuItem.sort)).all()
    return templates.TemplateResponse("owner/cafe.html",
        {"request": request, "cafe": cafe, "categories": cats, "items": items})

# ---------- HTMX/JSON Actions (efisien) ----------
@router.post("/api/categories/create", response_class=HTMLResponse)
def api_cat_create(
    cafe_id: int = Form(...), name: str = Form(...), sort: int = Form(1),
    user=Depends(get_current_user_from_cookie),
    db: Session = Depends(get_session),
):
    cafe = db.get(Cafe, cafe_id)
    if not cafe or cafe.owner_id != user.id: raise HTTPException(404)
    cat = Category(cafe_id=cafe_id, name=name, sort=sort)
    db.add(cat); db.commit(); db.refresh(cat)
    return templates.TemplateResponse("owner/partials/category_row.html", {"cat": cat})

@router.post("/api/items/create", response_class=HTMLResponse)
def api_item_create(
    cafe_id: int = Form(...), category_id: int = Form(...),
    name: str = Form(...), price_cents: int = Form(...),
    description: str | None = Form(None), sort: int = Form(1),
    user=Depends(get_current_user_from_cookie),
    db: Session = Depends(get_session),
):
    cafe = db.get(Cafe, cafe_id)
    if not cafe or cafe.owner_id != user.id: raise HTTPException(404)
    it = MenuItem(cafe_id=cafe_id, category_id=category_id, name=name,
                  price_cents=price_cents, description=description, sort=sort, is_active=True)
    db.add(it); db.commit(); db.refresh(it)
    return templates.TemplateResponse("owner/partials/item_card.html", {"it": it})

@router.post("/api/items/{item_id}/toggle", response_class=HTMLResponse)
def api_item_toggle(item_id: int,
    user=Depends(get_current_user_from_cookie),
    db: Session = Depends(get_session),
):
    it = db.get(MenuItem, item_id)
    if not it: raise HTTPException(404)
    cafe = db.get(Cafe, it.cafe_id)
    if not cafe or cafe.owner_id != user.id: raise HTTPException(404)
    it.is_active = not bool(it.is_active)
    db.add(it); db.commit(); db.refresh(it)
    return templates.TemplateResponse("owner/partials/item_card.html", {"it": it})

@router.post("/api/items/reorder")
def api_items_reorder(
    cafe_id: int = Form(...), ids: str = Form(...),
    user=Depends(get_current_user_from_cookie),
    db: Session = Depends(get_session),
):
    # ids = "12,5,8,3" berdasarkan urutan baru (SortableJS)
    id_list = [int(x) for x in ids.split(",") if x.strip().isdigit()]
    for idx, iid in enumerate(id_list, start=1):
        it = db.get(MenuItem, iid)
        if it and db.get(Cafe, it.cafe_id).owner_id == user.id:
            it.sort = idx; db.add(it)
    db.commit()
    return {"ok": True}

@router.post("/api/items/{item_id}/upload")
def api_item_upload(
    item_id: int, file: UploadFile = File(...),
    user=Depends(get_current_user_from_cookie),
    db: Session = Depends(get_session),
):
    it = db.get(MenuItem, item_id)
    if not it: raise HTTPException(404)
    cafe = db.get(Cafe, it.cafe_id)
    if not cafe or cafe.owner_id != user.id: raise HTTPException(404)

    # 1) presign
    key = f"cafes/{cafe.id}/menu/{item_id}/{file.filename}"
    pre = presign_upload(content_type=file.content_type or "image/jpeg", object_path=key)
    url, fields, public_url = pre["url"], pre["fields"], pre["public_url"]

    # 2) upload langsung ke R2
    data = {k: (None, v) for k, v in fields.items()}
    files = {"file": (file.filename, file.file, file.content_type)}
    with httpx.Client(timeout=30) as c:
        r = c.post(url, data=data, files=files)
        if r.status_code not in (204, 201, 200): raise HTTPException(500, "Upload failed")

    # 3) simpan url
    it.image_url = public_url
    db.add(it); db.commit(); db.refresh(it)
    return {"image_url": it.image_url}
