"""
Models for SME Questionnaires and Chat Messages.

This module provides the database schema for:
- Questionnaires (SME questionnaire sessions linked to assessments)
- Chat messages (conversation history within questionnaires)
"""

from datetime import datetime
from enum import Enum as EnumType
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy import Enum as EnumColumn
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import Mapped, relationship

from fides.api.db.base_class import Base

if TYPE_CHECKING:
    from fides.api.models.privacy_assessment import PrivacyAssessment


class QuestionnaireStatus(str, EnumType):
    """Status of a questionnaire session."""

    in_progress = "in_progress"
    completed = "completed"
    abandoned = "abandoned"


class Questionnaire(Base):
    """
    A questionnaire session linked to a privacy assessment.

    Tracks the interactive SME questionnaire sent via Slack or other
    chat providers, including progress, reminders, and conversation history.
    Answers collected through the questionnaire are persisted to the
    existing AssessmentAnswer/AnswerVersion tables with answer_source=team_input.

    Relationship: An assessment may have multiple questionnaire attempts
    (e.g., retries after abandonment). The ``PrivacyAssessment.questionnaire``
    relationship uses ``uselist=False`` and returns the latest active
    session; lookups by assessment_id should order by ``created_at desc``.
    """

    @declared_attr
    def __tablename__(self) -> str:
        return "questionnaire"

    assessment_id = Column(
        String,
        ForeignKey("privacy_assessment.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title = Column(String, nullable=False)
    status = Column(
        EnumColumn(QuestionnaireStatus),
        default=QuestionnaireStatus.in_progress,
        nullable=False,
        index=True,
    )
    current_question_index = Column(Integer, nullable=False, default=0)

    # Provider metadata: channel_id, channel_name, thread_id, thread_url, provider
    provider_context = Column(JSONB, server_default="{}", nullable=False)

    completed_at = Column(DateTime(timezone=True), nullable=True)
    last_reminder_at = Column(DateTime(timezone=True), nullable=True)
    reminder_count = Column(Integer, nullable=False, default=0)

    # Relationships
    assessment: Mapped["PrivacyAssessment"] = relationship(
        "PrivacyAssessment", back_populates="questionnaire"
    )
    messages: Mapped[List["ChatMessage"]] = relationship(
        "ChatMessage",
        back_populates="questionnaire",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="ChatMessage.timestamp",
    )

    @property
    def last_activity_at(self) -> Optional[datetime]:
        """Derived from the latest ChatMessage timestamp."""
        if self.messages:
            return max(m.timestamp for m in self.messages if m.timestamp)
        return self.created_at


class ChatMessage(Base):
    """
    A single message in a questionnaire conversation.

    Tracks per-message sender info to support multiple SMEs
    participating in the same questionnaire thread.
    """

    @declared_attr
    def __tablename__(self) -> str:
        return "chat_message"

    questionnaire_id = Column(
        String,
        ForeignKey("questionnaire.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    message_id = Column(String, nullable=True)  # Provider-specific ID (e.g. Slack ts)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    sender_email = Column(String, nullable=True, index=True)
    sender_display_name = Column(String, nullable=True)
    text = Column(Text, nullable=False)
    is_bot_message = Column(Boolean, nullable=False, default=False)
    question_index = Column(Integer, nullable=True)  # Which question this relates to

    # Relationships
    questionnaire = relationship("Questionnaire", back_populates="messages")
