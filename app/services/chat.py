from datetime import datetime
from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc
from sqlalchemy.orm import selectinload

from app.models.chat import ChatConversation, ChatMessage
from app.models.users import User
from app.schemas.chat import ConversationCreate, ChatMessageCreate


async def get_or_create_conversation(
    db: AsyncSession, admin_id: int, psicologo_id: int
) -> ChatConversation:
    """Get existing conversation or create new one between admin and psicologo"""
    # Check if conversation exists
    stmt = select(ChatConversation).where(
        and_(
            ChatConversation.id_admin == admin_id,
            ChatConversation.id_psicologo == psicologo_id,
        )
    )
    result = await db.execute(stmt)
    conversation = result.scalar_one_or_none()

    if conversation:
        return conversation

    # Create new conversation
    conversation = ChatConversation(id_admin=admin_id, id_psicologo=psicologo_id)
    db.add(conversation)
    await db.commit()
    await db.refresh(conversation)
    return conversation


async def list_conversations_for_user(
    db: AsyncSession, user_id: int, is_admin: bool
) -> List[Tuple[ChatConversation, str, int]]:
    """
    List all conversations for a user with participant names and unread count
    Returns: List of (conversation, participant_name, unread_count)
    """
    if is_admin:
        # Admin sees conversations with psicologos
        stmt = (
            select(
                ChatConversation,
                User.nombre,
                User.apellido,
                func.count(ChatMessage.id_mensaje)
                .filter(
                    and_(
                        ChatMessage.id_receiver == user_id, ChatMessage.is_read == False
                    )
                )
                .label("unread_count"),
            )
            .join(User, ChatConversation.id_psicologo == User.id_usuario)
            .outerjoin(
                ChatMessage,
                ChatConversation.id_conversacion == ChatMessage.id_conversacion,
            )
            .where(ChatConversation.id_admin == user_id)
            .group_by(ChatConversation.id_conversacion, User.nombre, User.apellido)
            .order_by(desc(ChatConversation.updated_at))
        )
    else:
        # Psicologo sees conversations with admins
        stmt = (
            select(
                ChatConversation,
                User.nombre,
                User.apellido,
                func.count(ChatMessage.id_mensaje)
                .filter(
                    and_(
                        ChatMessage.id_receiver == user_id, ChatMessage.is_read == False
                    )
                )
                .label("unread_count"),
            )
            .join(User, ChatConversation.id_admin == User.id_usuario)
            .outerjoin(
                ChatMessage,
                ChatConversation.id_conversacion == ChatMessage.id_conversacion,
            )
            .where(ChatConversation.id_psicologo == user_id)
            .group_by(ChatConversation.id_conversacion, User.nombre, User.apellido)
            .order_by(desc(ChatConversation.updated_at))
        )

    result = await db.execute(stmt)
    rows = result.all()

    conversations_with_details = []
    for row in rows:
        conversation = row[0]
        nombre = row[1]
        apellido = row[2]
        unread_count = row[3] if len(row) > 3 else 0
        participant_name = f"{nombre} {apellido}"
        conversations_with_details.append(
            (conversation, participant_name, unread_count)
        )

    return conversations_with_details


async def get_conversation(
    db: AsyncSession, conversation_id: int
) -> Optional[ChatConversation]:
    """Get conversation by ID"""
    stmt = select(ChatConversation).where(
        ChatConversation.id_conversacion == conversation_id
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def is_user_in_conversation(
    db: AsyncSession, conversation_id: int, user_id: int
) -> bool:
    """Check if user is participant in conversation"""
    conversation = await get_conversation(db, conversation_id)
    if not conversation:
        return False
    return conversation.id_admin == user_id or conversation.id_psicologo == user_id


async def list_messages(
    db: AsyncSession, conversation_id: int, skip: int = 0, limit: int = 100
) -> List[ChatMessage]:
    """Get messages in a conversation"""
    stmt = (
        select(ChatMessage)
        .where(ChatMessage.id_conversacion == conversation_id)
        .order_by(ChatMessage.created_at.asc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def create_message(
    db: AsyncSession, conversation_id: int, sender_id: int, receiver_id: int, texto: str
) -> ChatMessage:
    """Create a new message in conversation"""
    # Validate that sender and receiver are participants
    conversation = await get_conversation(db, conversation_id)
    if not conversation:
        raise ValueError("Conversation not found")

    participants = {conversation.id_admin, conversation.id_psicologo}
    if sender_id not in participants or receiver_id not in participants:
        raise ValueError("Sender or receiver not in conversation")

    # Create message
    message = ChatMessage(
        id_conversacion=conversation_id,
        id_sender=sender_id,
        id_receiver=receiver_id,
        texto=texto,
    )
    db.add(message)

    # Update conversation metadata
    conversation.updated_at = datetime.utcnow()
    conversation.last_message_at = datetime.utcnow()
    conversation.last_message_text = texto[:500] if len(texto) > 500 else texto

    await db.commit()
    await db.refresh(message)

    return message


async def mark_messages_as_read(
    db: AsyncSession, conversation_id: int, user_id: int
) -> int:
    """Mark all messages in conversation as read for user"""
    from sqlalchemy import update

    stmt = (
        update(ChatMessage)
        .where(
            and_(
                ChatMessage.id_conversacion == conversation_id,
                ChatMessage.id_receiver == user_id,
                ChatMessage.is_read == False,
            )
        )
        .values(is_read=True)
    )
    result = await db.execute(stmt)
    await db.commit()
    return result.rowcount


async def get_conversation_participants(
    db: AsyncSession, conversation_id: int
) -> Optional[Tuple[int, int]]:
    """Get admin_id and psicologo_id for a conversation"""
    conversation = await get_conversation(db, conversation_id)
    if not conversation:
        return None
    return (conversation.id_admin, conversation.id_psicologo)
