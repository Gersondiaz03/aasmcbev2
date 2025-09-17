from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.deps import get_db
from app.models.notificacion import Notificacion
from app.schemas.notificacion import NotificacionCreate, NotificacionRead
from app.core.ws import manager

router = APIRouter()


@router.post("/", response_model=NotificacionRead, status_code=status.HTTP_201_CREATED)
async def create_notification(
    notification_in: NotificacionCreate, db: AsyncSession = Depends(get_db)
):
    noti = Notificacion(**notification_in.model_dump())
    db.add(noti)
    await db.commit()
    await db.refresh(noti)
    target_users = []
    id_est = getattr(noti, "id_estudiante", None)
    id_psi = getattr(noti, "id_psicologo", None)
    if id_est:
        target_users.append(id_est)
    if id_psi and id_psi != id_est:
        target_users.append(id_psi)
    for uid in target_users:
        await manager.send_to_user(
            uid,
            {
                "type": "notification_new",
                "data": NotificacionRead.from_orm(noti).model_dump(),
            },
        )
    return noti


@router.get("/user/{user_id}", response_model=list[NotificacionRead])
async def list_notifications(user_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Notificacion)
        .where(
            (Notificacion.id_estudiante == user_id)
            | (Notificacion.id_psicologo == user_id)
        )
        .order_by(Notificacion.fecha_creacion.desc())
    )
    return result.scalars().all()


@router.patch("/{notification_id}/read", response_model=NotificacionRead)
async def mark_as_read(notification_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Notificacion).where(Notificacion.id_notificacion == notification_id)
    )
    noti = result.scalar_one_or_none()
    if not noti:
        raise HTTPException(status_code=404, detail="Notificación no encontrada")
    setattr(noti, "leida", True)
    await db.commit()
    await db.refresh(noti)
    targets = []
    id_est = getattr(noti, "id_estudiante", None)
    id_psi = getattr(noti, "id_psicologo", None)
    if id_est:
        targets.append(id_est)
    if id_psi and id_psi != id_est:
        targets.append(id_psi)
    for uid in targets:
        await manager.send_to_user(
            uid, {"type": "notification_read", "id": noti.id_notificacion}
        )
    return noti


@router.delete("/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_notification(notification_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Notificacion).where(Notificacion.id_notificacion == notification_id)
    )
    noti = result.scalar_one_or_none()
    if not noti:
        raise HTTPException(status_code=404, detail="Notificación no encontrada")
    targets = []
    id_est = getattr(noti, "id_estudiante", None)
    id_psi = getattr(noti, "id_psicologo", None)
    if id_est:
        targets.append(id_est)
    if id_psi and id_psi != id_est:
        targets.append(id_psi)
    await db.delete(noti)
    await db.commit()
    for uid in targets:
        await manager.send_to_user(
            uid, {"type": "notification_deleted", "id": notification_id}
        )
    return None


@router.delete("/user/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_all_notifications(user_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Notificacion).where(
            (Notificacion.id_estudiante == user_id)
            | (Notificacion.id_psicologo == user_id)
        )
    )
    notis = result.scalars().all()
    for n in notis:
        await db.delete(n)
    await db.commit()
    await manager.send_to_user(user_id, {"type": "notifications_cleared"})
    return None
