from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


# Message schemas
class ChatMessageBase(BaseModel):
    texto: str


class ChatMessageCreate(BaseModel):
    id_receiver: int
    texto: str


class ChatMessageRead(BaseModel):
    id_mensaje: int
    id_conversacion: int
    id_sender: int
    id_receiver: int
    texto: str
    created_at: datetime
    is_read: bool

    model_config = ConfigDict(from_attributes=True)


# Conversation schemas
class ConversationBase(BaseModel):
    id_admin: int
    id_psicologo: int


class ConversationCreate(BaseModel):
    id_psicologo: int  # admin initiates conversation with psicologo


class ConversationRead(BaseModel):
    id_conversacion: int
    id_admin: int
    id_psicologo: int
    created_at: datetime
    updated_at: datetime
    last_message_at: Optional[datetime] = None
    last_message_text: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ConversationWithDetails(ConversationRead):
    admin_nombre: Optional[str] = None
    psicologo_nombre: Optional[str] = None
    unread_count: int = 0
