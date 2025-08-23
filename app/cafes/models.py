# app/cafes/models.py
from typing import Optional
from sqlmodel import SQLModel, Field

class Cafe(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    slug: str | None = Field(default=None, unique=True, index=True)
    description: Optional[str] = None
    owner_id: int = Field(index=True)
    brand_color: Optional[str] = None
    wa_phone: Optional[str] = None
