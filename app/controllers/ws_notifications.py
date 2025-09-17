from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from jose import jwt, JWTError
from sqlalchemy.future import select

from app.core.ws import manager
from app.models.notificacion import Notificacion
from app.core.config import settings


router = APIRouter()

SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm


@router.websocket("/ws/notifications")
async def websocket_endpoint(websocket: WebSocket, token: str = Query(...)):
    # Accept early to avoid 403 during handshake; close with custom code on failure
    await websocket.accept()
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        sub = payload.get("sub")
        if sub is None:
            raise JWTError("Missing sub")
        user_id = int(sub)
    except (JWTError, ValueError, TypeError):
        await websocket.close(code=4401)
        return

    await manager.connect(user_id, websocket)

    # Send initial count of unread notifications
    try:
        # Lazy import to avoid circular app
        from app.core.database import AsyncSessionLocal

        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Notificacion).where(
                    (
                        (Notificacion.id_estudiante == user_id)
                        | (Notificacion.id_psicologo == user_id)
                    )
                    & (Notificacion.leida == False)  # noqa: E712
                )
            )
            unread_count = len(result.scalars().all())
            await websocket.send_json({"type": "unread_count", "count": unread_count})
    except Exception:  # noqa: BLE001 - keep connection open on failure
        # Don't terminate connection on initial count failure
        pass

    try:
        while True:
            # Keep connection open; optionally receive pings
            _ = await websocket.receive_text()
            # Echo ping-pong
            await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        manager.disconnect(user_id, websocket)
