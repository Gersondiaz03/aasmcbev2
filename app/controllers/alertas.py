from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from app.core.deps import get_db
from app.models.alerta import Alerta
from app.models.users import User
from app.models.roles import Role
from app.models.notificacion import Notificacion
from app.schemas.alerta import AlertaCreate, AlertaRead
from app.schemas.notificacion import NotificacionRead
from app.core.ws import manager

router = APIRouter()


@router.post("/", response_model=AlertaRead, status_code=status.HTTP_201_CREATED)
async def crear_alerta(alert_in: AlertaCreate, db: AsyncSession = Depends(get_db)):
    # Validate student exists
    res_user = await db.execute(
        select(User).where(User.id_usuario == alert_in.id_estudiante)
    )
    estudiante = res_user.scalar_one_or_none()
    if not estudiante:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")

    alerta = Alerta(**alert_in.model_dump())
    db.add(alerta)
    await db.commit()
    await db.refresh(alerta)

    # Build human-readable info for notifications
    estudiante_nombre = f"{getattr(estudiante, 'nombre', '')} {getattr(estudiante, 'apellido', '')}".strip()
    titulo_base = (
        f"ALERTA {alerta.severidad}: {estudiante_nombre} ({estudiante.email}) a las "
        f"{alerta.fecha_creacion} dijo: '{alerta.texto[:150]}{'...' if len(alerta.texto) > 150 else ''}'"
    )

    # Find ADMIN and PSICOLOGO users
    res_roles = await db.execute(select(Role))
    roles = {r.nombre_rol: r.id_rol for r in res_roles.scalars().all()}
    admin_role_id = roles.get("ADMINISTRADOR")
    psicologo_role_id = roles.get("PSICOLOGO")

    target_users: List[int] = []
    if admin_role_id:
        res_admins = await db.execute(select(User).where(User.id_rol == admin_role_id))
        target_users.extend([u.id_usuario for u in res_admins.scalars().all()])
    if psicologo_role_id:
        res_psis = await db.execute(
            select(User).where(User.id_rol == psicologo_role_id)
        )
        target_users.extend([u.id_usuario for u in res_psis.scalars().all()])

    # Create Notificaciones for each target
    for uid in set(target_users):
        n = Notificacion(
            id_estudiante=alerta.id_estudiante,
            id_psicologo=uid,
            titulo=titulo_base,
        )
        db.add(n)
        await db.commit()
        await db.refresh(n)
        # Standard notification push so existing panels update
        await manager.send_to_user(
            uid,
            {
                "type": "notification_new",
                "data": NotificacionRead.from_orm(n).model_dump(),
            },
        )
        # Extra event for specialized UIs if needed
        await manager.send_to_user(
            uid,
            {
                "type": "alerta_nueva",
                "data": {
                    "id_alerta": alerta.id_alerta,
                    "id_estudiante": alerta.id_estudiante,
                    "texto": alerta.texto,
                    "severidad": alerta.severidad,
                    "fecha_creacion": str(alerta.fecha_creacion),
                    "estudiante_nombre": estudiante_nombre,
                    "estudiante_email": estudiante.email,
                },
            },
        )

    return alerta


@router.get("/", response_model=list[AlertaRead])
async def listar_alertas(db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Alerta).order_by(Alerta.fecha_creacion.desc()))
    return res.scalars().all()


@router.get("/user/{id_estudiante}", response_model=list[AlertaRead])
async def listar_alertas_usuario(
    id_estudiante: int, db: AsyncSession = Depends(get_db)
):
    res = await db.execute(
        select(Alerta)
        .where(Alerta.id_estudiante == id_estudiante)
        .order_by(Alerta.fecha_creacion.desc())
    )
    return res.scalars().all()
