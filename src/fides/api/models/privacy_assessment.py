"""
Models for Privacy Assessment and Answer History Store.

This module provides the database schema for:
- Assessment templates (versioned DPIA/PIA definitions)
- Assessment questions (linked to templates, grouped by requirement)
- Privacy assessments (instances linked to systems/declarations)
- Assessment answers (current answer state)
- Answer versions (immutable history of all answer changes)
"""

from enum import Enum as EnumType
from sqlalchemy import (
    ARRAY,
    Boolean,
    Column,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy import Enum as EnumColumn
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import relationship

from fides.api.db.base_class import Base


class AssessmentStatus(str, EnumType):
    """Status of a privacy assessment."""

    in_progress = "in_progress"
    completed = "completed"
    outdated = "outdated"


class RiskLevel(str, EnumType):
    """Risk level of a privacy assessment."""

    high = "high"
    medium = "medium"
    low = "low"


class AnswerStatus(str, EnumType):
    """Status of an assessment answer."""

    complete = "complete"
    partial = "partial"
    needs_input = "needs_input"


class AnswerSource(str, EnumType):
    """Source of an assessment answer."""

    system = "system"
    ai_analysis = "ai_analysis"
    user_input = "user_input"
    team_input = "team_input"


class AnswerChangeType(str, EnumType):
    """Type of change to an answer version."""

    ai_generated = "ai_generated"
    human_edited = "human_edited"
    approved = "approved"
    rejected = "rejected"


class AssessmentTemplate(Base):
    """
    Versioned assessment template definitions.

    Each template represents a specific version of a DPIA/PIA assessment type
    (e.g., GDPR DPIA v1.0, CPRA Risk Assessment 2024-03-29).

    Template versions are identified by a standardized format:
    ORGANIZATION-ASSESSMENT-YYYY-MM-DD (e.g., CPPA-CPRA-RA-2024-03-29)
    """

    @declared_attr
    def __tablename__(self) -> str:
        return "assessment_template"

    key = Column(String, unique=True, nullable=False, index=True)
    version = Column(String, nullable=False)
    name = Column(String, nullable=False)
    assessment_type = Column(String, nullable=False, default="dpia")  # dpia, cpra, etc.
    region = Column(String, nullable=False)
    authority = Column(String, nullable=True)
    legal_reference = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    questions = relationship(
        "AssessmentQuestion",
        back_populates="template",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    assessments = relationship(
        "PrivacyAssessment",
        back_populates="template",
    )


class AssessmentQuestion(Base):
    """
    Questions belonging to an assessment template.

    Questions are grouped by requirement_key (e.g., "processing_scope").
    Each group has a shared requirement_title for display (e.g., "Processing Scope and Purpose(s)").
    """

    @declared_attr
    def __tablename__(self) -> str:
        return "assessment_question"

    template_id = Column(
        String,
        ForeignKey("assessment_template.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Grouping fields
    requirement_key = Column(String, nullable=False, index=True)
    requirement_title = Column(String, nullable=False)  # Human-readable group title
    group_order = Column(Integer, nullable=False, default=0)  # Order of this group

    # Question fields
    question_key = Column(String, nullable=False)
    question_text = Column(Text, nullable=False)
    guidance = Column(Text, nullable=True)
    question_order = Column(Integer, nullable=False, default=0)  # Order within group
    required = Column(Boolean, default=True, nullable=False)
    fides_sources = Column(ARRAY(String), server_default="{}", nullable=False)
    expected_coverage = Column(String, default="none", nullable=False)

    # Relationships
    template = relationship("AssessmentTemplate", back_populates="questions")
    answers = relationship(
        "AssessmentAnswer",
        back_populates="question",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class PrivacyAssessment(Base):
    """
    An assessment instance linked to a specific system/declaration.

    Represents a concrete assessment being conducted using a specific template.
    """

    @declared_attr
    def __tablename__(self) -> str:
        return "privacy_assessment"

    template_id = Column(
        String,
        ForeignKey("assessment_template.id"),
        nullable=False,
        index=True,
    )
    name = Column(String, nullable=False)
    status = Column(
        EnumColumn(AssessmentStatus),
        default=AssessmentStatus.in_progress,
        nullable=False,
        index=True,
    )
    risk_level = Column(
        EnumColumn(RiskLevel),
        nullable=True,
    )
    completeness = Column(Float, default=0.0, nullable=False)

    # System/Declaration context
    system_fides_key = Column(String, nullable=False, index=True)
    system_name = Column(String, nullable=True)
    declaration_id = Column(String, nullable=True, index=True)
    declaration_name = Column(String, nullable=True)
    data_use = Column(String, nullable=True)
    data_use_name = Column(String, nullable=True)
    data_categories = Column(ARRAY(String), server_default="{}", nullable=False)

    # Creator tracking
    created_by = Column(String, nullable=True, index=True)

    # Relationships
    template = relationship("AssessmentTemplate", back_populates="assessments")
    answers = relationship(
        "AssessmentAnswer",
        back_populates="assessment",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    # uselist=False returns the most recently loaded questionnaire row.
    # Multiple attempts may exist (see Questionnaire model docstring);
    # for explicit "latest" semantics, query with order_by(created_at.desc()).
    questionnaire = relationship(
        "Questionnaire",
        back_populates="assessment",
        cascade="all, delete-orphan",
        passive_deletes=True,
        uselist=False,
    )


class AssessmentAnswer(Base):
    """
    Current answer for each question in an assessment.

    This table stores the current state of each answer. The full history
    of changes is stored in the AnswerVersion table.
    """

    @declared_attr
    def __tablename__(self) -> str:
        return "assessment_answer"

    assessment_id = Column(
        String,
        ForeignKey("privacy_assessment.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    question_id = Column(
        String,
        ForeignKey("assessment_question.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    current_version_id = Column(
        String,
        ForeignKey(
            "answer_version.id",
            ondelete="SET NULL",
            use_alter=True,
            name="fk_assessment_answer_current_version_id",
        ),
        nullable=True,
    )

    # Relationships
    assessment = relationship("PrivacyAssessment", back_populates="answers")
    question = relationship("AssessmentQuestion", back_populates="answers")
    current_version = relationship(
        "AnswerVersion",
        foreign_keys=[current_version_id],
        post_update=True,
    )
    versions = relationship(
        "AnswerVersion",
        back_populates="answer",
        foreign_keys="AnswerVersion.answer_id",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="AnswerVersion.version_number.desc()",
    )


class AnswerVersion(Base):
    """
    Immutable history of all answer versions.

    Each modification to an answer creates a new version record.
    This provides a complete audit trail of all changes.
    """

    @declared_attr
    def __tablename__(self) -> str:
        return "answer_version"

    answer_id = Column(
        String,
        ForeignKey("assessment_answer.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    version_number = Column(Integer, nullable=False, default=1)

    # Answer content
    answer_text = Column(Text, nullable=True)
    answer_status = Column(
        EnumColumn(AnswerStatus),
        default=AnswerStatus.needs_input,
        nullable=False,
    )
    answer_source = Column(
        EnumColumn(AnswerSource),
        default=AnswerSource.system,
        nullable=False,
    )
    confidence = Column(Float, nullable=True)

    # Change metadata
    change_type = Column(
        EnumColumn(AnswerChangeType),
        nullable=False,
        index=True,
    )
    created_by = Column(String, nullable=False, index=True)

    # Evidence and source references (JSONB for flexibility)
    evidence = Column(JSONB, server_default="{}", nullable=False)
    source_references = Column(JSONB, server_default="{}", nullable=False)

    # Diff from previous version (for display)
    diff_from_previous = Column(Text, nullable=True)

    # Relationships
    answer = relationship(
        "AssessmentAnswer",
        back_populates="versions",
        foreign_keys=[answer_id],
    )
