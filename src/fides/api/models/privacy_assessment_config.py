"""SQLAlchemy model for privacy assessment configuration."""

from sqlalchemy import Boolean, Column, String
from sqlalchemy.ext.declarative import declared_attr

from fides.api.db.base_class import Base

# Default LLM models for assessments
DEFAULT_ASSESSMENT_MODEL = "openrouter/anthropic/claude-opus-4"
DEFAULT_CHAT_MODEL = "openrouter/google/gemini-2.5-flash"


class PrivacyAssessmentConfig(Base):
    """
    Stores configuration for privacy assessments.

    This is a single-row table per tenant. The single record describes
    global assessment configuration settings including:
    - LLM model overrides for assessment execution and chat
    - Re-assessment scheduling (cron expression)
    - Slack channel for questionnaire notifications
    """

    @declared_attr
    def __tablename__(self) -> str:
        return "privacy_assessment_config"

    # LLM Configuration
    assessment_model_override = Column(
        String,
        nullable=True,
        comment="Custom LLM model for running assessments. If null, uses default.",
    )
    chat_model_override = Column(
        String,
        nullable=True,
        comment="Custom LLM model for questionnaire chat. If null, uses default.",
    )

    # Re-assessment Scheduling
    reassessment_enabled = Column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
        comment="Whether automatic re-assessment is enabled.",
    )
    reassessment_cron = Column(
        String(100),
        nullable=False,
        default="0 9 * * *",
        server_default="0 9 * * *",
        comment="Cron expression for re-assessment schedule. Default: daily at 9am.",
    )
    reassessment_timezone = Column(
        String(50),
        nullable=False,
        default="UTC",
        server_default="UTC",
        comment="Timezone for the cron schedule.",
    )

    # Slack Configuration
    slack_channel_id = Column(
        String,
        nullable=True,
        comment="Slack channel ID for questionnaire notifications.",
    )
    slack_channel_name = Column(
        String,
        nullable=True,
        comment="Slack channel name (for display purposes).",
    )

    @classmethod
    def get_assessment_model(cls, config: "PrivacyAssessmentConfig | None") -> str:
        """Get the effective assessment model, using default if not configured."""
        if config and config.assessment_model_override:
            return config.assessment_model_override
        return DEFAULT_ASSESSMENT_MODEL

    @classmethod
    def get_chat_model(cls, config: "PrivacyAssessmentConfig | None") -> str:
        """Get the effective chat model, using default if not configured."""
        if config and config.chat_model_override:
            return config.chat_model_override
        return DEFAULT_CHAT_MODEL
