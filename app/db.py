from sqlmodel import SQLModel, Field, create_engine, Session, select
from typing import Optional
from datetime import datetime, timedelta
from .config import settings
engine = create_engine(settings.DATABASE_URL, echo=False)
class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True)
    password_hash: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
class Cafe(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    owner_id: int = Field(foreign_key="user.id")
    name: str
    slug: str = Field(index=True, unique=True)
    logo_url: Optional[str] = None
    theme: Optional[str] = "default"
    timezone: Optional[str] = "Asia/Jakarta"
    created_at: datetime = Field(default_factory=datetime.utcnow)
class Subscription(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    cafe_id: int = Field(foreign_key="cafe.id", index=True)
    plan_code: str = "free"
    status: str = "active"
    started_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime = Field(default_factory=lambda: datetime.utcnow() + timedelta(days=365*10))
    payment_ref: Optional[str] = None
class Category(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    cafe_id: int = Field(foreign_key="cafe.id", index=True)
    name: str
    sort: int = 0
class MenuItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    cafe_id: int = Field(foreign_key="cafe.id", index=True)
    category_id: Optional[int] = Field(default=None, foreign_key="category.id")
    name: str
    price_cents: int
    description: Optional[str] = None
    image_url: Optional[str] = None
    tags_json: Optional[str] = None
    stock: Optional[int] = None
    is_active: bool = True
    sort: int = 0
def init_db():
    SQLModel.metadata.create_all(engine)
def get_session():
    with Session(engine) as session:
        yield session
