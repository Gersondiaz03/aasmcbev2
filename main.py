from contextlib import asynccontextmanager
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.controllers.auth import router as auth
from app.controllers.disponibilidad import router as disponibilidad
from app.controllers.roles import router as roles_router
from app.controllers.citas import router as citas_router
from app.controllers.users import router as users_router
from app.controllers.notifications import router as notifications_router
from app.controllers.observaciones import router as observaciones_router
from app.controllers.alertas import router as alertas_router
from app.controllers.ws_notifications import router as ws_notifications_router
from app.controllers.chat import router as chat_router
from app.models.roles import Role
from fastapi.responses import RedirectResponse


@asynccontextmanager
async def lifespan(_: FastAPI):
    from app.core.database import AsyncSessionLocal

    async with AsyncSessionLocal() as session:
        await seed_roles(session)
    yield


app = FastAPI(title="AASMC API", lifespan=lifespan)

app.include_router(roles_router, prefix="/roles", tags=["Roles"])
app.include_router(users_router, prefix="/users", tags=["Usuarios"])
app.include_router(citas_router, prefix="/citas", tags=["Citas"])
app.include_router(auth, prefix="/auth", tags=["auth"])
app.include_router(
    disponibilidad, prefix="/disponibilidad", tags=["DisponibilidadDocente"]
)
app.include_router(
    notifications_router, prefix="/notifications", tags=["Notificaciones"]
)
app.include_router(
    observaciones_router, prefix="/observaciones", tags=["Observaciones"]
)
app.include_router(alertas_router, prefix="/alertas", tags=["Alertas"])
app.include_router(chat_router)
app.include_router(ws_notifications_router)

origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://aasmc.vercel.app",
    "https://aasmcv2.vercel.app",
    "https://aasmcagentv2.onrender.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def enforce_https(request: Request, call_next):
    # Skip redirect logic for WebSocket handshake requests
    # WebSocket connections start as an HTTP GET with Upgrade headers
    upgrade = request.headers.get("upgrade", "").lower()
    if upgrade == "websocket":
        return await call_next(request)

    proto = request.headers.get("x-forwarded-proto", "http")
    app_env_mw = os.getenv("APP_ENV", "development")
    if app_env_mw == "production":
        proto = request.headers.get("x-forwarded-proto", "http")
        if proto != "https":
            url = request.url.replace(scheme="https")
            return RedirectResponse(url, status_code=301)
    return await call_next(request)


@app.get("/health", tags=["General"])
async def health_check():
    return {"status": "ok"}


async def seed_roles(db: AsyncSession):
    roles = ["ADMINISTRADOR", "PSICOLOGO", "ESTUDIANTE"]
    for nombre in roles:
        result = await db.execute(select(Role).where(Role.nombre_rol == nombre))
        rol = result.scalars().first()
        if not rol:
            db.add(Role(nombre_rol=nombre))
    await db.commit()


if __name__ == "__main__":
    app_env = os.getenv("APP_ENV", "development")
    # Railway and similar platforms inject the PORT environment variable
    port = int(os.getenv("PORT", "8000"))

    if app_env == "production":
        uvicorn.run("app.main:app", host="0.0.0.0", port=port)
    else:  # development
        uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)
