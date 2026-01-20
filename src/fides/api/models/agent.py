"""
SQLAlchemy models for the AI Privacy Analyst Agent feature.

These models support the conversational AI interface that allows users
to query their data map using natural language.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any, List, Optional

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Session, relationship

from fides.api.db.base_class import Base

if TYPE_CHECKING:
    from fides.api.models.fides_user import FidesUser


class AgentSettings(Base):
    """
    Singleton table for organization-level agent settings.

    Stores compliance frameworks and custom system prompt configuration
    that applies to all agent conversations.
    """

    __tablename__ = "agent_settings"

    compliance_frameworks = Column(
        ARRAY(String()),
        server_default="{}",
        nullable=False,
        doc="List of compliance framework identifiers (e.g., 'GDPR', 'CCPA', 'HIPAA')",
    )
    custom_system_prompt = Column(
        Text(),
        nullable=True,
        doc="Custom instructions to append to the agent's system prompt",
    )

    @classmethod
    def get_or_create(cls, db: Session) -> "AgentSettings":
        """Get the singleton settings record, creating it if it doesn't exist."""
        settings = db.query(cls).first()
        if settings is None:
            settings = cls(compliance_frameworks=[], custom_system_prompt=None)
            db.add(settings)
            db.commit()
            db.refresh(settings)
        return settings


class AgentConversation(Base):
    """
    Represents a chat conversation session between a user and the AI agent.

    Each conversation contains multiple messages and is associated with
    a specific Fides user.
    """

    __tablename__ = "agent_conversation"

    user_id = Column(
        String(255),
        ForeignKey("fidesuser.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="The ID of the user who owns this conversation",
    )
    title = Column(
        String(500),
        nullable=True,
        doc="Auto-generated or user-provided title for the conversation",
    )
    is_archived = Column(
        Boolean(),
        server_default="false",
        nullable=False,
        doc="Whether the conversation has been archived by the user",
    )

    # Relationships
    user: "FidesUser" = relationship(
        "FidesUser",
        back_populates="agent_conversations",
        lazy="joined",
    )
    messages: List["AgentMessage"] = relationship(
        "AgentMessage",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="AgentMessage.created_at",
        lazy="dynamic",
    )

    @classmethod
    def get_by_user(
        cls,
        db: Session,
        user_id: str,
        include_archived: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> List["AgentConversation"]:
        """Get all conversations for a specific user."""
        query = db.query(cls).filter(cls.user_id == user_id)
        if not include_archived:
            query = query.filter(cls.is_archived == False)  # noqa: E712
        return (
            query.order_by(cls.updated_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    @classmethod
    def count_by_user(cls, db: Session, user_id: str, include_archived: bool = False) -> int:
        """Count conversations for a specific user."""
        query = db.query(cls).filter(cls.user_id == user_id)
        if not include_archived:
            query = query.filter(cls.is_archived == False)  # noqa: E712
        return query.count()

    def get_messages(
        self, db: Session, limit: Optional[int] = None
    ) -> List["AgentMessage"]:
        """Get messages in this conversation, ordered by creation time."""
        query = db.query(AgentMessage).filter(
            AgentMessage.conversation_id == self.id
        ).order_by(AgentMessage.created_at)
        if limit:
            query = query.limit(limit)
        return query.all()

    def auto_generate_title(self, db: Session) -> Optional[str]:
        """
        Generate a title from the first user message if title is not set.

        Returns the new title or None if title already exists or no messages.
        """
        if self.title:
            return None

        first_message = (
            db.query(AgentMessage)
            .filter(
                AgentMessage.conversation_id == self.id,
                AgentMessage.role == "user",
            )
            .order_by(AgentMessage.created_at)
            .first()
        )

        if first_message and first_message.content:
            # Truncate to first 100 chars for title
            title = first_message.content[:100]
            if len(first_message.content) > 100:
                title = title.rsplit(" ", 1)[0] + "..."
            self.title = title
            db.add(self)
            db.commit()
            return title
        return None


class AgentMessage(Base):
    """
    Represents a single message in an agent conversation.

    Messages can be from the user, the assistant, or tool responses.
    Tool calls made by the assistant are stored in the tool_calls field.
    """

    __tablename__ = "agent_message"

    conversation_id = Column(
        String(255),
        ForeignKey("agent_conversation.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="The conversation this message belongs to",
    )
    role = Column(
        String(50),
        nullable=False,
        doc="Message role: 'user', 'assistant', or 'tool'",
    )
    content = Column(
        Text(),
        nullable=True,
        doc="The text content of the message",
    )
    tool_calls = Column(
        JSONB(astext_type=Text()),
        nullable=True,
        doc="Tool calls made by the assistant (JSON array)",
    )
    tool_call_id = Column(
        String(255),
        nullable=True,
        doc="For tool messages, the ID of the tool call this responds to",
    )
    model_used = Column(
        String(100),
        nullable=True,
        doc="The LLM model used for this response",
    )
    prompt_tokens = Column(
        Integer(),
        nullable=True,
        doc="Number of tokens in the prompt",
    )
    completion_tokens = Column(
        Integer(),
        nullable=True,
        doc="Number of tokens in the completion",
    )

    # Relationships
    conversation: "AgentConversation" = relationship(
        "AgentConversation",
        back_populates="messages",
    )

    @classmethod
    def create_user_message(
        cls,
        db: Session,
        conversation_id: str,
        content: str,
    ) -> "AgentMessage":
        """Create a user message in a conversation."""
        message = cls(
            conversation_id=conversation_id,
            role="user",
            content=content,
        )
        db.add(message)
        db.commit()
        db.refresh(message)
        return message

    @classmethod
    def create_assistant_message(
        cls,
        db: Session,
        conversation_id: str,
        content: Optional[str] = None,
        tool_calls: Optional[List[dict]] = None,
        model_used: Optional[str] = None,
        prompt_tokens: Optional[int] = None,
        completion_tokens: Optional[int] = None,
    ) -> "AgentMessage":
        """Create an assistant message in a conversation."""
        message = cls(
            conversation_id=conversation_id,
            role="assistant",
            content=content,
            tool_calls=tool_calls,
            model_used=model_used,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
        )
        db.add(message)
        db.commit()
        db.refresh(message)
        return message

    @classmethod
    def create_tool_message(
        cls,
        db: Session,
        conversation_id: str,
        tool_call_id: str,
        content: str,
    ) -> "AgentMessage":
        """Create a tool response message in a conversation."""
        message = cls(
            conversation_id=conversation_id,
            role="tool",
            tool_call_id=tool_call_id,
            content=content,
        )
        db.add(message)
        db.commit()
        db.refresh(message)
        return message


class AgentEmbedding(Base):
    """
    Stores vector embeddings for entity content to enable semantic search.

    Each entity (system, dataset, etc.) has its content converted to a
    text representation, hashed for change detection, and embedded as
    a 768-dimensional vector for similarity search.
    """

    __tablename__ = "agent_embedding"

    entity_type = Column(
        String(100),
        nullable=False,
        index=True,
        doc="Type of entity: 'system', 'dataset', 'privacy_declaration', etc.",
    )
    entity_id = Column(
        String(255),
        nullable=False,
        index=True,
        doc="The ID of the entity this embedding represents",
    )
    content_hash = Column(
        String(64),
        nullable=False,
        doc="SHA-256 hash of source_text for change detection",
    )
    source_text = Column(
        Text(),
        nullable=False,
        doc="The text content that was embedded",
    )
    # Note: The 'embedding' vector column is created via raw SQL in the migration
    # It's not defined here as SQLAlchemy doesn't have native pgvector support
    # Access it via raw SQL queries or the pgvector Python library

    @classmethod
    def get_by_entity(
        cls, db: Session, entity_type: str, entity_id: str
    ) -> Optional["AgentEmbedding"]:
        """Get embedding for a specific entity."""
        return (
            db.query(cls)
            .filter(cls.entity_type == entity_type, cls.entity_id == entity_id)
            .first()
        )

    @classmethod
    def delete_by_entity(cls, db: Session, entity_type: str, entity_id: str) -> bool:
        """Delete embedding for a specific entity. Returns True if deleted."""
        result = (
            db.query(cls)
            .filter(cls.entity_type == entity_type, cls.entity_id == entity_id)
            .delete()
        )
        db.commit()
        return result > 0

    @classmethod
    def get_stats(cls, db: Session) -> dict[str, Any]:
        """Get statistics about the embedding index."""
        from sqlalchemy import func

        total = db.query(func.count(cls.id)).scalar()
        by_type = dict(
            db.query(cls.entity_type, func.count(cls.id))
            .group_by(cls.entity_type)
            .all()
        )
        oldest = db.query(func.min(cls.updated_at)).scalar()
        newest = db.query(func.max(cls.updated_at)).scalar()

        return {
            "total_embeddings": total,
            "by_entity_type": by_type,
            "oldest_updated_at": oldest,
            "newest_updated_at": newest,
        }


class AgentEmbeddingQueue(Base):
    """
    Queue table for asynchronous embedding updates.

    Database triggers automatically add entries to this queue when
    entities are created, updated, or deleted. A background task
    processes the queue to update embeddings.
    """

    __tablename__ = "agent_embedding_queue"

    # Composite primary key: (entity_type, entity_id)
    entity_type = Column(
        String(100),
        primary_key=True,
        nullable=False,
        doc="Type of entity that changed",
    )
    entity_id = Column(
        String(255),
        primary_key=True,
        nullable=False,
        doc="ID of the entity that changed",
    )
    operation = Column(
        String(20),
        nullable=False,
        doc="Type of change: 'insert', 'update', or 'delete'",
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default="now()",
        nullable=False,
        index=True,
        doc="When the change was queued",
    )
    processed_at = Column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
        doc="When the queue entry was processed (null if pending)",
    )

    # Override the id column since we use composite primary key
    id = None  # type: ignore

    @classmethod
    def get_pending(cls, db: Session, limit: int = 100) -> List["AgentEmbeddingQueue"]:
        """Get pending queue entries to process."""
        return (
            db.query(cls)
            .filter(cls.processed_at == None)  # noqa: E711
            .order_by(cls.created_at)
            .limit(limit)
            .all()
        )

    @classmethod
    def mark_processed(
        cls, db: Session, entity_type: str, entity_id: str
    ) -> None:
        """Mark a queue entry as processed."""
        db.query(cls).filter(
            cls.entity_type == entity_type, cls.entity_id == entity_id
        ).update({"processed_at": datetime.utcnow()})
        db.commit()

    @classmethod
    def count_pending(cls, db: Session) -> int:
        """Count pending queue entries."""
        return db.query(cls).filter(cls.processed_at == None).count()  # noqa: E711

    @classmethod
    def clear_processed(cls, db: Session, older_than_hours: int = 24) -> int:
        """Remove processed entries older than specified hours."""
        from sqlalchemy import func

        cutoff = func.now() - func.make_interval(0, 0, 0, 0, older_than_hours)
        result = (
            db.query(cls)
            .filter(cls.processed_at != None, cls.processed_at < cutoff)  # noqa: E711
            .delete()
        )
        db.commit()
        return result
