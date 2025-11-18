from typing import List
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
    Query,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from jose import jwt, JWTError

from app.core.deps import get_db
from app.core.security import get_current_user
from app.core.ws_chat import chat_manager
from app.core.config import settings
from app.models.users import User
from app.models.roles import Role
from app.schemas.chat import (
    ConversationCreate,
    ConversationRead,
    ConversationWithDetails,
    ChatMessageCreate,
    ChatMessageRead,
)
from app.services import chat as chat_service


router = APIRouter(prefix="/chat", tags=["chat"])


@router.get("/psicologos", response_model=List[dict])
async def list_psicologos(
    current_user_id: str = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """List all psychologists for admin to start conversations"""
    user_id = int(current_user_id)
    user, role = await get_user_with_role(db, user_id)

    # Only admin can list psychologists
    if role.nombre_rol != "ADMINISTRADOR":
        raise HTTPException(status_code=403, detail="Only admin can list psychologists")

    # Get all psychologists
    stmt = (
        select(User, Role)
        .join(Role, User.id_rol == Role.id_rol)
        .where(Role.nombre_rol == "PSICOLOGO")
    )
    result = await db.execute(stmt)
    rows = result.all()

    psicologos = []
    for user, role in rows:
        psicologos.append(
            {
                "id_usuario": user.id_usuario,
                "nombre": user.nombre,
                "apellido": user.apellido,
                "email": user.email,
            }
        )

    return psicologos


@router.get("/admins", response_model=List[dict])
async def list_admins(
    current_user_id: str = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """List all admins for psychologist to start conversations"""
    user_id = int(current_user_id)
    user, role = await get_user_with_role(db, user_id)

    # Only psychologist can list admins
    if role.nombre_rol != "PSICOLOGO":
        raise HTTPException(status_code=403, detail="Only psychologist can list admins")

    # Get all admins
    stmt = (
        select(User, Role)
        .join(Role, User.id_rol == Role.id_rol)
        .where(Role.nombre_rol == "ADMINISTRADOR")
    )
    result = await db.execute(stmt)
    rows = result.all()

    admins = []
    for user, role in rows:
        admins.append(
            {
                "id_usuario": user.id_usuario,
                "nombre": user.nombre,
                "apellido": user.apellido,
                "email": user.email,
            }
        )

    return admins


async def get_user_with_role(db: AsyncSession, user_id: int):
    """Get user with role information"""
    stmt = (
        select(User, Role)
        .join(Role, User.id_rol == Role.id_rol)
        .where(User.id_usuario == user_id)
    )
    result = await db.execute(stmt)
    row = result.one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="User not found")
    return row[0], row[1]


@router.post("/conversations", response_model=ConversationRead)
async def create_or_get_conversation(
    data: ConversationCreate,
    current_user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create or get existing conversation between admin and psicologo"""
    user_id = int(current_user_id)
    user, role = await get_user_with_role(db, user_id)

    admin_id = None
    psicologo_id = None

    if role.nombre_rol == "ADMINISTRADOR":
        # Admin creating conversation with psicologo
        admin_id = user_id
        psicologo_id = data.id_psicologo

        # Verify psicologo exists and has correct role
        psicologo, psicologo_role = await get_user_with_role(db, data.id_psicologo)
        if psicologo_role.nombre_rol != "PSICOLOGO":
            raise HTTPException(
                status_code=400, detail="Target user must be a psicologo"
            )

    elif role.nombre_rol == "PSICOLOGO":
        # Psicologo creating conversation with admin
        psicologo_id = user_id
        admin_id = (
            data.id_psicologo
        )  # In this case, id_psicologo field contains admin_id

        # Verify admin exists and has correct role
        admin, admin_role = await get_user_with_role(db, data.id_psicologo)
        if admin_role.nombre_rol != "ADMINISTRADOR":
            raise HTTPException(status_code=400, detail="Target user must be an admin")

    else:
        raise HTTPException(
            status_code=403, detail="Only admin or psicologo can create conversations"
        )

    conversation = await chat_service.get_or_create_conversation(
        db=db, admin_id=admin_id, psicologo_id=psicologo_id
    )

    return conversation


@router.get("/conversations", response_model=List[ConversationWithDetails])
async def list_conversations(
    current_user_id: str = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """List all conversations for current user"""
    user_id = int(current_user_id)
    user, role = await get_user_with_role(db, user_id)

    is_admin = role.nombre_rol == "ADMINISTRADOR"

    conversations_data = await chat_service.list_conversations_for_user(
        db=db, user_id=user_id, is_admin=is_admin
    )

    # Build response with details
    result = []
    for conversation, participant_name, unread_count in conversations_data:
        result.append(
            ConversationWithDetails(
                id_conversacion=conversation.id_conversacion,
                id_admin=conversation.id_admin,
                id_psicologo=conversation.id_psicologo,
                created_at=conversation.created_at,
                updated_at=conversation.updated_at,
                last_message_at=conversation.last_message_at,
                last_message_text=conversation.last_message_text,
                admin_nombre=participant_name if not is_admin else None,
                psicologo_nombre=participant_name if is_admin else None,
                unread_count=unread_count,
            )
        )

    return result


@router.get(
    "/conversations/{conversation_id}/messages", response_model=List[ChatMessageRead]
)
async def get_messages(
    conversation_id: int,
    skip: int = 0,
    limit: int = 100,
    current_user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get messages in a conversation"""
    user_id = int(current_user_id)

    # Verify user is participant
    is_participant = await chat_service.is_user_in_conversation(
        db=db, conversation_id=conversation_id, user_id=user_id
    )

    if not is_participant:
        raise HTTPException(
            status_code=403, detail="Not authorized to view this conversation"
        )

    messages = await chat_service.list_messages(
        db=db, conversation_id=conversation_id, skip=skip, limit=limit
    )

    return messages


@router.post(
    "/conversations/{conversation_id}/messages", response_model=ChatMessageRead
)
async def send_message(
    conversation_id: int,
    message_data: ChatMessageCreate,
    current_user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Send a message in a conversation"""
    user_id = int(current_user_id)

    # Verify user is participant
    is_participant = await chat_service.is_user_in_conversation(
        db=db, conversation_id=conversation_id, user_id=user_id
    )

    if not is_participant:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to send messages in this conversation",
        )

    try:
        message = await chat_service.create_message(
            db=db,
            conversation_id=conversation_id,
            sender_id=user_id,
            receiver_id=message_data.id_receiver,
            texto=message_data.texto,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Broadcast to WebSocket connections
    await chat_manager.broadcast(
        conversation_id=conversation_id,
        message={
            "type": "new_message",
            "message": {
                "id_mensaje": message.id_mensaje,
                "id_conversacion": message.id_conversacion,
                "id_sender": message.id_sender,
                "id_receiver": message.id_receiver,
                "texto": message.texto,
                "created_at": message.created_at.isoformat(),
                "is_read": message.is_read,
            },
        },
    )

    return message


@router.post("/conversations/{conversation_id}/read")
async def mark_as_read(
    conversation_id: int,
    current_user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark all messages in conversation as read"""
    user_id = int(current_user_id)

    # Verify user is participant
    is_participant = await chat_service.is_user_in_conversation(
        db=db, conversation_id=conversation_id, user_id=user_id
    )

    if not is_participant:
        raise HTTPException(status_code=403, detail="Not authorized")

    count = await chat_service.mark_messages_as_read(
        db=db, conversation_id=conversation_id, user_id=user_id
    )

    return {"marked_read": count}


@router.websocket("/ws/{conversation_id}")
async def websocket_chat(
    websocket: WebSocket, conversation_id: int, token: str = Query(...)
):
    """WebSocket endpoint for real-time chat"""
    # Accept connection first
    await websocket.accept()

    # Authenticate
    try:
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.algorithm]
        )
        sub = payload.get("sub")
        if sub is None:
            raise JWTError("Missing sub")
        user_id = int(sub)
    except (JWTError, ValueError, TypeError):
        await websocket.close(code=4401)
        return

    # Verify user is participant
    from app.core.database import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        is_participant = await chat_service.is_user_in_conversation(
            db=db, conversation_id=conversation_id, user_id=user_id
        )

        if not is_participant:
            await websocket.close(code=4403)
            return

    # Connect to chat
    await chat_manager.connect(conversation_id, websocket)

    try:
        while True:
            # Keep connection open; receive pings
            data = await websocket.receive_text()
            # Echo pong
            if data == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        chat_manager.disconnect(conversation_id, websocket)
