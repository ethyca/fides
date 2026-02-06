"""add privacy assessment schema

Revision ID: b2c3d4e5f6g7
Revises: a1b2c3d4e5f7
Create Date: 2026-02-05 15:00:00.000000

"""

import uuid
from datetime import datetime, timezone

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "b2c3d4e5f6g7"
down_revision = "a1b2c3d4e5f7"
branch_labels = None
depends_on = None


def generate_id(prefix: str) -> str:
    """Generate a prefixed UUID."""
    return f"{prefix}_{uuid.uuid4()}"


# Assessment Templates
ASSESSMENT_TEMPLATES = [
    {
        "key": "us_ca_cpra_risk_assessment",
        "version": "US-CA-CPPA-RA-2024-03-29",
        "name": "California CPRA / CCPA Risk Assessment",
        "assessment_type": "cpra",
        "region": "United States (California)",
        "authority": "California Privacy Protection Agency",
        "legal_reference": "CPPA regulations effective 2026 (risk assessments)",
        "description": "Risk assessment for processing that presents significant risk to consumers' privacy.",
        "is_active": True,
    },
    {
        "key": "gdpr_dpia",
        "version": "EU-GDPR-DPIA-2018-05-25",
        "name": "GDPR Data Protection Impact Assessment (DPIA)",
        "assessment_type": "dpia",
        "region": "EU/EEA",
        "authority": "EU GDPR",
        "legal_reference": "GDPR Article 35 (DPIA) and Article 36 (Prior consultation)",
        "description": "Assessment required when processing is likely to result in a high risk to individuals' rights and freedoms.",
        "is_active": True,
    },
]

# CPRA Questions organized by requirement group (matching POC structure)
CPRA_QUESTIONS = [
    # Group 1: Processing Scope and Purpose(s)
    {
        "requirement_key": "processing_scope",
        "requirement_title": "Processing Scope and Purpose(s)",
        "group_order": 1,
        "questions": [
            {
                "question_key": "cpra_1_1",
                "question_text": "What is the name and description of this processing activity?",
                "guidance": "Describe the processing activity including its business purpose.",
                "question_order": 1,
                "required": True,
                "fides_sources": [
                    "system.name",
                    "system.description",
                    "privacy_declaration.name",
                ],
                "expected_coverage": "partial",
            },
            {
                "question_key": "cpra_1_2",
                "question_text": "What are the specific purposes for processing personal information?",
                "guidance": "List all purposes/data uses for this processing activity.",
                "question_order": 2,
                "required": True,
                "fides_sources": [
                    "privacy_declaration.data_use",
                    "data_use.name",
                    "data_use.description",
                ],
                "expected_coverage": "full",
            },
            {
                "question_key": "cpra_1_3",
                "question_text": "Why is this processing necessary for the business?",
                "guidance": "Explain the business justification for this processing.",
                "question_order": 3,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
        ],
    },
    # Group 2: Significant Risk Determination
    {
        "requirement_key": "significant_risk_determination",
        "requirement_title": "Significant Risk Determination",
        "group_order": 2,
        "questions": [
            {
                "question_key": "cpra_2_1",
                "question_text": "Does this processing involve selling personal information?",
                "guidance": "'Selling' under CCPA includes exchanging PI for monetary or other valuable consideration.",
                "question_order": 1,
                "required": True,
                "fides_sources": ["privacy_declaration.data_use"],
                "expected_coverage": "partial",
            },
            {
                "question_key": "cpra_2_2",
                "question_text": "Does this processing involve sharing PI for cross-context behavioral advertising?",
                "guidance": "Cross-context behavioral advertising tracks consumers across different businesses/websites.",
                "question_order": 2,
                "required": True,
                "fides_sources": ["privacy_declaration.data_use", "data_use.name"],
                "expected_coverage": "partial",
            },
            {
                "question_key": "cpra_2_3",
                "question_text": "Does this processing involve sensitive personal information?",
                "guidance": "Sensitive PI includes SSN, financial info, precise geolocation, biometric data, health data, etc.",
                "question_order": 3,
                "required": True,
                "fides_sources": ["privacy_declaration.data_categories"],
                "expected_coverage": "full",
            },
            {
                "question_key": "cpra_2_4",
                "question_text": "Does this processing use automated decision-making technology (ADMT)?",
                "guidance": "ADMT includes profiling, AI/ML decisions that affect consumers.",
                "question_order": 4,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "partial",
            },
        ],
    },
    # Group 3: Data Categories
    {
        "requirement_key": "data_categories",
        "requirement_title": "Data Categories",
        "group_order": 3,
        "questions": [
            {
                "question_key": "cpra_3_1",
                "question_text": "What categories of personal information are collected and processed?",
                "guidance": "List all data categories using Fides taxonomy.",
                "question_order": 1,
                "required": True,
                "fides_sources": [
                    "privacy_declaration.data_categories",
                    "data_category.name",
                ],
                "expected_coverage": "full",
            },
            {
                "question_key": "cpra_3_2",
                "question_text": "What categories of sensitive personal information (SPI) are involved?",
                "guidance": "Identify all sensitive data categories (health, financial, biometric, etc.).",
                "question_order": 2,
                "required": True,
                "fides_sources": ["privacy_declaration.data_categories"],
                "expected_coverage": "full",
            },
        ],
    },
    # Group 4: Consumer Notification
    {
        "requirement_key": "consumer_notification",
        "requirement_title": "Consumer Notification",
        "group_order": 4,
        "questions": [
            {
                "question_key": "cpra_4_1",
                "question_text": "Where and how is this processing disclosed to consumers?",
                "guidance": "Identify privacy notices and collection points where consumers are informed.",
                "question_order": 1,
                "required": True,
                "fides_sources": ["privacy_notice.name", "privacy_notice.data_uses"],
                "expected_coverage": "full",
            },
            {
                "question_key": "cpra_4_2",
                "question_text": "Are just-in-time notices provided at collection points?",
                "guidance": "Document any point-of-collection notices beyond the privacy policy.",
                "question_order": 2,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "partial",
            },
        ],
    },
    # Group 5: Consumer Rights
    {
        "requirement_key": "consumer_rights",
        "requirement_title": "Consumer Rights",
        "group_order": 5,
        "questions": [
            {
                "question_key": "cpra_5_1",
                "question_text": "How can consumers exercise their CCPA rights for this processing?",
                "guidance": "Document mechanisms for: know, access, delete, correct, opt-out, limit use of SPI.",
                "question_order": 1,
                "required": True,
                "fides_sources": ["privacy_experience", "policy.drp_action"],
                "expected_coverage": "partial",
            },
        ],
    },
    # Group 6: Retention Periods
    {
        "requirement_key": "retention_periods",
        "requirement_title": "Retention Periods",
        "group_order": 6,
        "questions": [
            {
                "question_key": "cpra_6_1",
                "question_text": "How long is personal information retained for this processing?",
                "guidance": "Specify retention periods for each data category if different.",
                "question_order": 1,
                "required": True,
                "fides_sources": ["privacy_declaration.retention_period"],
                "expected_coverage": "partial",
            },
            {
                "question_key": "cpra_6_2",
                "question_text": "What is the legal or business justification for this retention period?",
                "guidance": "Explain why this retention period is necessary and appropriate.",
                "question_order": 2,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
        ],
    },
    # Group 7: Third-Party Recipients
    {
        "requirement_key": "third_party_recipients",
        "requirement_title": "Third-Party Recipients",
        "group_order": 7,
        "questions": [
            {
                "question_key": "cpra_7_1",
                "question_text": "What third parties receive personal information from this processing?",
                "guidance": "List all vendors, processors, and other recipients.",
                "question_order": 1,
                "required": True,
                "fides_sources": [
                    "privacy_declaration.third_parties",
                    "connection.name",
                ],
                "expected_coverage": "partial",
            },
            {
                "question_key": "cpra_7_2",
                "question_text": "What is the purpose of each third-party disclosure?",
                "guidance": "Document why data is shared with each recipient.",
                "question_order": 2,
                "required": True,
                "fides_sources": ["privacy_declaration.data_use"],
                "expected_coverage": "partial",
            },
        ],
    },
    # Group 8: Service Provider Contracts
    {
        "requirement_key": "service_provider_contracts",
        "requirement_title": "Service Provider Contracts",
        "group_order": 8,
        "questions": [
            {
                "question_key": "cpra_8_1",
                "question_text": "Do contracts with service providers include required CCPA provisions?",
                "guidance": "Contracts must restrict use/sale of PI and require assistance with consumer requests.",
                "question_order": 1,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
        ],
    },
    # Group 9: Technical Safeguards
    {
        "requirement_key": "technical_safeguards",
        "requirement_title": "Technical Safeguards",
        "group_order": 9,
        "questions": [
            {
                "question_key": "cpra_9_1",
                "question_text": "What technical security measures protect personal information?",
                "guidance": "Describe encryption, access controls, monitoring, etc.",
                "question_order": 1,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
            {
                "question_key": "cpra_9_2",
                "question_text": "How is access to personal information controlled and logged?",
                "guidance": "Document access controls and audit logging.",
                "question_order": 2,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
        ],
    },
    # Group 10: Benefits vs. Risks
    {
        "requirement_key": "benefits_vs_risks",
        "requirement_title": "Benefits vs. Risks Analysis",
        "group_order": 10,
        "questions": [
            {
                "question_key": "cpra_10_1",
                "question_text": "What are the benefits of this processing to the business?",
                "guidance": "Describe business value and operational benefits.",
                "question_order": 1,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
            {
                "question_key": "cpra_10_2",
                "question_text": "What are the benefits of this processing to consumers?",
                "guidance": "Describe how consumers benefit from this processing.",
                "question_order": 2,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
            {
                "question_key": "cpra_10_3",
                "question_text": "What are the potential negative impacts on consumers?",
                "guidance": "Identify privacy risks, potential harms, and other negative impacts.",
                "question_order": 3,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
            {
                "question_key": "cpra_10_4",
                "question_text": "Do the benefits outweigh the risks? Explain.",
                "guidance": "Provide a balanced assessment of benefits vs. risks.",
                "question_order": 4,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
        ],
    },
]


def upgrade() -> None:
    # Create assessment_template table
    op.create_table(
        "assessment_template",
        sa.Column("id", sa.String(length=255), nullable=False),
        sa.Column("key", sa.String(), nullable=False),
        sa.Column("version", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("assessment_type", sa.String(), nullable=False),
        sa.Column("region", sa.String(), nullable=False),
        sa.Column("authority", sa.String(), nullable=True),
        sa.Column("legal_reference", sa.Text(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("key"),
    )
    op.create_index("ix_assessment_template_key", "assessment_template", ["key"])

    # Create assessment_question table
    op.create_table(
        "assessment_question",
        sa.Column("id", sa.String(length=255), nullable=False),
        sa.Column("template_id", sa.String(), nullable=False),
        sa.Column("requirement_key", sa.String(), nullable=False),
        sa.Column("requirement_title", sa.String(), nullable=False),
        sa.Column("group_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("question_key", sa.String(), nullable=False),
        sa.Column("question_text", sa.Text(), nullable=False),
        sa.Column("guidance", sa.Text(), nullable=True),
        sa.Column("question_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("required", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "fides_sources",
            postgresql.ARRAY(sa.String()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column(
            "expected_coverage", sa.String(), nullable=False, server_default="none"
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["template_id"], ["assessment_template.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_assessment_question_template_id", "assessment_question", ["template_id"]
    )
    op.create_index(
        "ix_assessment_question_requirement_key",
        "assessment_question",
        ["requirement_key"],
    )

    # Create privacy_assessment table
    op.create_table(
        "privacy_assessment",
        sa.Column("id", sa.String(length=255), nullable=False),
        sa.Column("template_id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("in_progress", "completed", "outdated", name="assessmentstatus"),
            nullable=False,
            server_default="in_progress",
        ),
        sa.Column(
            "risk_level",
            sa.Enum("high", "medium", "low", name="risklevel"),
            nullable=True,
        ),
        sa.Column("completeness", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("system_fides_key", sa.String(), nullable=False),
        sa.Column("system_name", sa.String(), nullable=True),
        sa.Column("declaration_id", sa.String(), nullable=True),
        sa.Column("declaration_name", sa.String(), nullable=True),
        sa.Column("data_use", sa.String(), nullable=True),
        sa.Column("data_use_name", sa.String(), nullable=True),
        sa.Column(
            "data_categories",
            postgresql.ARRAY(sa.String()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column("created_by", sa.String(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["template_id"], ["assessment_template.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_privacy_assessment_template_id", "privacy_assessment", ["template_id"]
    )
    op.create_index(
        "ix_privacy_assessment_system_fides_key",
        "privacy_assessment",
        ["system_fides_key"],
    )
    op.create_index("ix_privacy_assessment_status", "privacy_assessment", ["status"])

    # Create answer_version table (before assessment_answer due to FK)
    op.create_table(
        "answer_version",
        sa.Column("id", sa.String(length=255), nullable=False),
        sa.Column("answer_id", sa.String(), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("answer_text", sa.Text(), nullable=True),
        sa.Column(
            "answer_status",
            sa.Enum("complete", "partial", "needs_input", name="answerstatus"),
            nullable=False,
            server_default="needs_input",
        ),
        sa.Column(
            "answer_source",
            sa.Enum(
                "system", "ai_analysis", "user_input", "slack", name="answersource"
            ),
            nullable=False,
            server_default="system",
        ),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column(
            "change_type",
            sa.Enum(
                "ai_generated",
                "human_edited",
                "approved",
                "rejected",
                name="answerchangetype",
            ),
            nullable=False,
        ),
        sa.Column("created_by", sa.String(), nullable=False),
        sa.Column("evidence", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column(
            "source_references", postgresql.JSONB(), nullable=False, server_default="{}"
        ),
        sa.Column("diff_from_previous", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_answer_version_answer_id", "answer_version", ["answer_id"])
    op.create_index("ix_answer_version_change_type", "answer_version", ["change_type"])
    op.create_index("ix_answer_version_created_by", "answer_version", ["created_by"])

    # Create assessment_answer table
    op.create_table(
        "assessment_answer",
        sa.Column("id", sa.String(length=255), nullable=False),
        sa.Column("assessment_id", sa.String(), nullable=False),
        sa.Column("question_id", sa.String(), nullable=False),
        sa.Column("current_version_id", sa.String(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["assessment_id"], ["privacy_assessment.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["question_id"], ["assessment_question.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["current_version_id"], ["answer_version.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_assessment_answer_assessment_id", "assessment_answer", ["assessment_id"]
    )
    op.create_index(
        "ix_assessment_answer_question_id", "assessment_answer", ["question_id"]
    )

    # Add FK from answer_version to assessment_answer (deferred due to circular reference)
    op.create_foreign_key(
        "fk_answer_version_answer_id",
        "answer_version",
        "assessment_answer",
        ["answer_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # Seed assessment templates
    conn = op.get_bind()
    now = datetime.now(timezone.utc)

    for template_data in ASSESSMENT_TEMPLATES:
        template_id = generate_id("ast")
        conn.execute(
            sa.text("""
                INSERT INTO assessment_template (id, key, version, name, assessment_type, region, authority, legal_reference, description, is_active, created_at, updated_at)
                VALUES (:id, :key, :version, :name, :assessment_type, :region, :authority, :legal_reference, :description, :is_active, :created_at, :updated_at)
            """),
            {
                "id": template_id,
                "key": template_data["key"],
                "version": template_data["version"],
                "name": template_data["name"],
                "assessment_type": template_data["assessment_type"],
                "region": template_data["region"],
                "authority": template_data["authority"],
                "legal_reference": template_data["legal_reference"],
                "description": template_data["description"],
                "is_active": template_data["is_active"],
                "created_at": now,
                "updated_at": now,
            },
        )

        # Seed CPRA questions for the CPRA template
        if template_data["key"] == "us_ca_cpra_risk_assessment":
            for group in CPRA_QUESTIONS:
                for question in group["questions"]:
                    question_id = generate_id("asq")
                    conn.execute(
                        sa.text("""
                            INSERT INTO assessment_question (id, template_id, requirement_key, requirement_title, group_order, question_key, question_text, guidance, question_order, required, fides_sources, expected_coverage, created_at, updated_at)
                            VALUES (:id, :template_id, :requirement_key, :requirement_title, :group_order, :question_key, :question_text, :guidance, :question_order, :required, :fides_sources, :expected_coverage, :created_at, :updated_at)
                        """),
                        {
                            "id": question_id,
                            "template_id": template_id,
                            "requirement_key": group["requirement_key"],
                            "requirement_title": group["requirement_title"],
                            "group_order": group["group_order"],
                            "question_key": question["question_key"],
                            "question_text": question["question_text"],
                            "guidance": question["guidance"],
                            "question_order": question["question_order"],
                            "required": question["required"],
                            "fides_sources": question["fides_sources"],
                            "expected_coverage": question["expected_coverage"],
                            "created_at": now,
                            "updated_at": now,
                        },
                    )


def downgrade() -> None:
    # Drop FK first
    op.drop_constraint(
        "fk_answer_version_answer_id", "answer_version", type_="foreignkey"
    )

    # Drop tables in reverse order
    op.drop_table("assessment_answer")
    op.drop_table("answer_version")
    op.drop_table("privacy_assessment")
    op.drop_table("assessment_question")
    op.drop_table("assessment_template")

    # Drop enums
    op.execute("DROP TYPE IF EXISTS answerchangetype")
    op.execute("DROP TYPE IF EXISTS answersource")
    op.execute("DROP TYPE IF EXISTS answerstatus")
    op.execute("DROP TYPE IF EXISTS risklevel")
    op.execute("DROP TYPE IF EXISTS assessmentstatus")
