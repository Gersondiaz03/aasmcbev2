import unicodedata
from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import Date, cast, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.deps import get_db
from app.models.disponibilidad import DisponibilidadPsicologo
from app.models.citas import Cita
from app.schemas.disponibilidad import (
    DisponibilidadCreate,
    DisponibilidadRead,
    HorarioLibre,
)

router = APIRouter()


# Crear disponibilidad
@router.post(
    "/", response_model=DisponibilidadRead, status_code=status.HTTP_201_CREATED
)
async def create_disponibilidad(
    disponibilidad_in: DisponibilidadCreate,
    db: AsyncSession = Depends(get_db),
):
    disponibilidad = DisponibilidadPsicologo(
        id_psicologo=disponibilidad_in.id_psicologo,
        dia_semana=disponibilidad_in.dia_semana,
        hora_inicio=disponibilidad_in.hora_inicio,
        hora_fin=disponibilidad_in.hora_fin,
    )
    db.add(disponibilidad)
    await db.commit()
    await db.refresh(disponibilidad)
    # Construir el objeto de respuesta manualmente para cumplir con el schema
    return DisponibilidadRead(
        id_disponibilidad=disponibilidad.id_disponibilidad,
        id_psicologo=disponibilidad.id_psicologo,
        dia_semana=disponibilidad.dia_semana,
        hora_inicio=disponibilidad.hora_inicio,
        hora_fin=disponibilidad.hora_fin,
    )


# Listar disponibilidad por psicólogo (todas sus citas)
@router.get(
    "/{id_psicologo}/cita/{id_cita}",
    response_model=list[DisponibilidadRead],
)
async def list_disponibilidad_psicologo_cita(
    id_psicologo: int,
    id_cita: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(DisponibilidadPsicologo).where(
            DisponibilidadPsicologo.id_psicologo == id_psicologo,
        )
    )
    return result.scalars().all()


@router.get(
    "/{id_psicologo}/cita/{id_cita}/libres",
    response_model=list[HorarioLibre],
)
async def list_horarios_libres(
    id_psicologo: int,
    fecha: date = Query(..., description="Fecha en formato YYYY-MM-DD"),
    db: AsyncSession = Depends(get_db),
):
    dias = ["LUNES", "MARTES", "MIERCOLES", "JUEVES", "VIERNES", "SABADO", "DOMINGO"]
    dia_semana = dias[fecha.weekday()]
    print(
        f"[DEBUG] fecha={fecha} fecha.weekday()={fecha.weekday()} dia_semana={dia_semana}"
    )

    q_disp = await db.execute(
        select(DisponibilidadPsicologo).where(
            DisponibilidadPsicologo.id_psicologo == id_psicologo,
            func.upper(DisponibilidadPsicologo.dia_semana) == dia_semana,
        )
    )
    franjas = q_disp.scalars().all()
    print(f"[DEBUG] Franjas encontradas para dia_semana={dia_semana}: {franjas}")
    # 2) Trae las tutorías ocupadas ese día
    q_tuts = await db.execute(
        select(Cita).where(
            Cita.id_psicologo == id_psicologo,
            cast(Cita.fecha_hora_inicio, Date) == fecha,
        )
    )
    tuts = q_tuts.scalars().all()
    print(f"[DEBUG] Citas ocupadas ese día: {tuts}")

    ocupado_times = [
        (tut.fecha_hora_inicio.time(), tut.fecha_hora_fin.time()) for tut in tuts
    ]

    libres: list[dict] = []
    for f in franjas:
        # Ensure we get the actual Python time object, not a SQLAlchemy Column
        hora_inicio = getattr(f, "hora_inicio", None)
        hora_fin = getattr(f, "hora_fin", None)
        from datetime import time as dt_time

        if not isinstance(hora_inicio, dt_time) or not isinstance(hora_fin, dt_time):
            print(f"[DEBUG] Franja ignorada por tipo: {f}")
            continue
        inicio_dt = datetime.combine(fecha, hora_inicio)
        fin_dt = datetime.combine(fecha, hora_fin)
        current_slot_start_dt = inicio_dt
        while current_slot_start_dt + timedelta(hours=1) <= fin_dt:
            slot_inicio_time = current_slot_start_dt.time()
            slot_fin_dt = current_slot_start_dt + timedelta(hours=1)
            slot_fin_time = slot_fin_dt.time()
            is_slot_ocupado = False
            for tut_start_time, tut_end_time in ocupado_times:
                if slot_inicio_time < tut_end_time and tut_start_time < slot_fin_time:
                    is_slot_ocupado = True
                    break
            if not is_slot_ocupado:
                libres.append(
                    {
                        "inicio": slot_inicio_time.strftime("%H:%M:%S"),
                        "fin": slot_fin_time.strftime("%H:%M:%S"),
                    }
                )
            current_slot_start_dt += timedelta(hours=1)
    print(f"[DEBUG] Horarios libres calculados: {libres}")
    return libres


def normaliza_dia(d: str) -> str:
    return (
        unicodedata.normalize("NFKD", d)
        .encode("ascii", "ignore")
        .decode("ascii")
        .lower()
        .strip()
    )


@router.get("/{id_psicologo}/cita/{id_cita}/dias", response_model=list[str])
async def dias_disponibles_psicologo_cita(
    id_psicologo: int,
    id_cita: int,
    db: AsyncSession = Depends(get_db),
):
    q = await db.execute(
        select(DisponibilidadPsicologo.dia_semana).where(
            DisponibilidadPsicologo.id_psicologo == id_psicologo,
            DisponibilidadPsicologo.id_cita == id_cita,
        )
    )
    dias = [row[0] for row in q.fetchall()]
    # Quita duplicados por si acaso
    return list(sorted(set(dias)))


# New endpoint: list free dates for a psychologist
@router.get(
    "/{id_psicologo}/dias_libres",
    response_model=list[str],
)
async def list_dias_libres(
    id_psicologo: int,
    start: date = Query(..., description="Fecha de inicio YYYY-MM-DD"),
    end: date = Query(..., description="Fecha de fin YYYY-MM-DD"),
    db: AsyncSession = Depends(get_db),
):
    # Fetch configured availability days for the psychologist
    q_disp = await db.execute(
        select(DisponibilidadPsicologo.dia_semana)
        .where(DisponibilidadPsicologo.id_psicologo == id_psicologo)
    )
    dias_config = [row[0].upper() for row in q_disp.fetchall()]

    # Map Spanish day names to weekday numbers (0=Monday)
    map_dia = {
        'LUNES': 0, 'MARTES': 1, 'MIERCOLES': 2,
        'JUEVES': 3, 'VIERNES': 4, 'SABADO': 5, 'DOMINGO': 6
    }
    disponibles_weekdays = {map_dia[d] for d in dias_config if d in map_dia}

    libres: list[str] = []
    current = start
    from datetime import timedelta
    while current <= end:
        wd = current.weekday()
        # Check if psychologist works this weekday
        if wd in disponibles_weekdays:
            # Check if any appointment exists on this date
            q_cita = await db.execute(
                select(func.count())
                .select_from(Cita)
                .where(
                    Cita.id_psicologo == id_psicologo,
                    cast(Cita.fecha_hora_inicio, Date) == current,
                )
            )
            total = q_cita.scalar_one()
            if total == 0:
                libres.append(current.isoformat())
        current += timedelta(days=1)
    # Sort dates descending
    libres.sort(reverse=True)
    return libres


@router.delete("/{id_disponibilidad}", status_code=204)
async def delete_disponibilidad(
    id_disponibilidad: int,
    db: AsyncSession = Depends(get_db),
):
    disponibilidad = await db.get(DisponibilidadPsicologo, id_disponibilidad)
    if not disponibilidad:
        raise HTTPException(status_code=404, detail="Disponibilidad no encontrada")
    await db.delete(disponibilidad)
    await db.commit()
    return None
