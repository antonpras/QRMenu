from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlmodel import Session, select
from passlib.hash import bcrypt
import jwt
from datetime import datetime, timedelta
from ..db import User, get_session
from .service import presign_upload
pre = presign_upload("image/jpeg", f"cafes/{cafe.id}/menu/{item.id}/{filename}")
from ..config import settings
router = APIRouter(prefix="/auth", tags=["auth"])
class RegisterIn(BaseModel):
    email: EmailStr
    password: str
class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
@router.post("/register", response_model=TokenOut)
def register(data: RegisterIn, session: Session = Depends(get_session)):
    existing = session.exec(select(User).where(User.email == data.email)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(email=data.email, password_hash=bcrypt.hash(data.password))
    session.add(user); session.commit(); session.refresh(user)
    token = _make_token(user.id, user.email)
    return TokenOut(access_token=token)
class LoginIn(BaseModel):
    email: EmailStr
    password: str
@router.post("/login", response_model=TokenOut)
def login(data: LoginIn, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.email == data.email)).first()
    if not user or not bcrypt.verify(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = _make_token(user.id, user.email)
    return TokenOut(access_token=token)
def _make_token(user_id: int, email: str) -> str:
    payload = {"sub": str(user_id), "email": email, "exp": datetime.utcnow() + timedelta(hours=24)}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")
