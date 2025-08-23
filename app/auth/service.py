from datetime import datetime, timedelta
from jose import jwt
from passlib.context import CryptContext

# Inisialisasi bcrypt untuk hash password
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT config (ambil dari ENV kalau bisa)
SECRET_KEY = "CHANGE_THIS_SECRET"  # taruh di .env → JWT_SECRET
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60


def hash_password(password: str) -> str:
    """Hash plain password pake bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifikasi password cocok/tidak."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Buat JWT access token untuk user login."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
