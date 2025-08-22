from fastapi import APIRouter
from fastapi.responses import RedirectResponse

router = APIRouter()

@router.get("/m/{slug}")
def menu_landing(slug: str):
    # redirect ke JSON publik sementara
    return RedirectResponse(url=f"/menu/public/{slug}")
