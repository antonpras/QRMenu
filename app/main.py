from fastapi import FastAPI
from .db import init_db
from .auth.router import router as auth_router
from .cafes.router import router as cafes_router
from fastapi.staticfiles import StaticFiles
from .menu.router import router as menu_router
from .media.router import router as media_router
from .qr.router import router as qr_router
from .public.router import router as public_router
from .billing.router import router as billing_router
from .billing.webhook import router as billing_webhook_router
def create_app():
    init_db()
    app = FastAPI(title="QRMenu+ Backend (Zeabur)")
    app.mount("/static", StaticFiles(directory="static"), name="static")
    app.include_router(auth_router)
    app.include_router(cafes_router)
    app.include_router(public_router)
    app.include_router(menu_router)
    app.include_router(media_router)
    app.include_router(qr_router)
    app.include_router(billing_router)
    app.include_router(billing_webhook_router)
    return app
    
app = create_app()


@app.get("/", tags=["health"])
def root():
    return {
        "service": "QRMenu+ Backend",
        "version": "0.1.0",
        "docs": "/docs",
        "status": "running"
    }
