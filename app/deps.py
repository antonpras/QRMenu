from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt
from pydantic import BaseModel
from .config import settings
bearer = HTTPBearer(auto_error=False)
class CurrentUser(BaseModel):
    user_id: int
    email: str
def get_current_user(creds: HTTPAuthorizationCredentials = Depends(bearer)) -> CurrentUser:
    if not creds:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(creds.credentials, settings.JWT_SECRET, algorithms=["HS256"])
        return CurrentUser(user_id=int(payload["sub"]), email=payload["email"])
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
