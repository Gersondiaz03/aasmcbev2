from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Boolean,
    Text,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import Base


class ChatConversation(Base):
    __tablename__ = "Conversaciones"

    id_conversacion = Column(Integer, primary_key=True, index=True)
    id_admin = Column(
        Integer,
        ForeignKey("Usuarios.id_usuario", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    id_psicologo = Column(
        Integer,
        ForeignKey("Usuarios.id_usuario", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    last_message_at = Column(DateTime(timezone=True), nullable=True)
    last_message_text = Column(String(500), nullable=True)

    __table_args__ = (
        UniqueConstraint("id_admin", "id_psicologo", name="uq_admin_psicologo"),
    )

    # Relationships
    messages = relationship(
        "ChatMessage", back_populates="conversation", cascade="all, delete-orphan"
    )
    admin = relationship("User", foreign_keys=[id_admin])
    psicologo = relationship("User", foreign_keys=[id_psicologo])


class ChatMessage(Base):
    __tablename__ = "Mensajes"

    id_mensaje = Column(Integer, primary_key=True, index=True)
    id_conversacion = Column(
        Integer,
        ForeignKey("Conversaciones.id_conversacion", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    id_sender = Column(
        Integer, ForeignKey("Usuarios.id_usuario", ondelete="CASCADE"), nullable=False
    )
    id_receiver = Column(
        Integer, ForeignKey("Usuarios.id_usuario", ondelete="CASCADE"), nullable=False
    )
    texto = Column(Text, nullable=False)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    is_read = Column(Boolean, default=False, server_default="false", nullable=False)

    # Relationships
    conversation = relationship("ChatConversation", back_populates="messages")
    sender = relationship("User", foreign_keys=[id_sender])
    receiver = relationship("User", foreign_keys=[id_receiver])
