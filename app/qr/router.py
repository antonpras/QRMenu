import io
import segno
from fastapi import APIRouter, Response
from ..config import settings
router = APIRouter(prefix="/qr", tags=["qr"])
@router.get("/menu/{cafe_slug}", response_class=Response)
def qr_menu(cafe_slug: str):
    target = f"{settings.BASE_PUBLIC_URL}/m/{cafe_slug}"
    qrcode = segno.make(target, error='h')
    buf = io.BytesIO()
    qrcode.save(buf, kind="svg", xmldecl=False, scale=8)
    return Response(content=buf.getvalue(), media_type="image/svg+xml")
