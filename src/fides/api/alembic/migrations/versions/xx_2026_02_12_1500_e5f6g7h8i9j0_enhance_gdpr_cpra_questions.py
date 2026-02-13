"""enhance GDPR DPIA and CPRA assessment questions

This migration adds missing questions identified during comprehensive review:

GDPR DPIA additions (based on EDPB WP248 Annex 2):
- DPO advice documentation
- Residual risk acceptance
- Review cycle / change management

California CPRA additions (based on CPPA Section 7150 regulations):
- ADMT logic and outputs detail
- External consultation (including AI bias experts)
- Specific negative impact categories

Revision ID: e5f6g7h8i9j0
Revises: d4e5f6g7h8i9
Create Date: 2026-02-12 15:00:00.000000

"""

import uuid
from datetime import datetime, timezone

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "e5f6g7h8i9j0"
down_revision = "d4e5f6g7h8i9"
branch_labels = None
depends_on = None


def generate_id(prefix: str) -> str:
    """Generate a prefixed UUID."""
    return f"{prefix}_{uuid.uuid4()}"


# Additional GDPR DPIA Questions (based on EDPB WP248 Annex 2 gaps)
GDPR_DPIA_ADDITIONAL_QUESTIONS = [
    # Add to Group 7: Consultation - new question for DPO advice details
    {
        "requirement_key": "consultation",
        "requirement_title": "Consultation and Prior Consultation",
        "group_order": 7,
        "questions": [
            {
                "question_key": "dpia_7_3",
                "question_text": "What advice did the DPO provide and how has it been addressed?",
                "guidance": "Per GDPR Article 35(2), document the DPO's specific recommendations and how each has been implemented or why not.",
                "question_order": 3,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
        ],
    },
    # New Group 8: Residual Risk and Sign-off
    {
        "requirement_key": "residual_risk_signoff",
        "requirement_title": "Residual Risk and Sign-off",
        "group_order": 8,
        "questions": [
            {
                "question_key": "dpia_8_1",
                "question_text": "What is the residual risk level after all mitigation measures are applied?",
                "guidance": "Assess whether the remaining risk is acceptable. If high residual risk remains, prior consultation with the supervisory authority is required under Article 36.",
                "question_order": 1,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
            {
                "question_key": "dpia_8_2",
                "question_text": "Who has approved this DPIA and accepted the residual risk?",
                "guidance": "Document the names, roles, and sign-off dates of the accountable decision-makers.",
                "question_order": 2,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
        ],
    },
    # New Group 9: Review Cycle
    {
        "requirement_key": "review_cycle",
        "requirement_title": "Review Cycle and Change Management",
        "group_order": 9,
        "questions": [
            {
                "question_key": "dpia_9_1",
                "question_text": "When will this DPIA be reviewed and by whom?",
                "guidance": "Per GDPR Article 35(11), DPIAs must be reviewed when there is a change in the risk. Establish a regular review schedule.",
                "question_order": 1,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
            {
                "question_key": "dpia_9_2",
                "question_text": "What changes would trigger a reassessment of this DPIA?",
                "guidance": "Identify specific triggers such as: new data categories, new purposes, technology changes, security incidents, or regulatory changes.",
                "question_order": 2,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
        ],
    },
]


# Additional California CPRA Questions (based on CPPA Section 7150 gaps)
CPRA_ADDITIONAL_QUESTIONS = [
    # Add to existing ADMT group (Group 2 in original) - more detailed questions
    {
        "requirement_key": "admt_details",
        "requirement_title": "Automated Decision-Making Technology Details",
        "group_order": 11,  # New group after existing 10
        "questions": [
            {
                "question_key": "cpra_11_1",
                "question_text": "If ADMT is used, describe the logic of the automated decision-making technology.",
                "guidance": "Per CPPA regulations, explain in plain language how the ADMT works and what factors influence its outputs.",
                "question_order": 1,
                "required": False,
                "fides_sources": [],
                "expected_coverage": "none",
            },
            {
                "question_key": "cpra_11_2",
                "question_text": "What outputs does the ADMT generate and how are they used in significant decisions?",
                "guidance": "Describe the specific outputs (scores, classifications, recommendations) and how they affect decisions about consumers.",
                "question_order": 2,
                "required": False,
                "fides_sources": [],
                "expected_coverage": "none",
            },
        ],
    },
    # New Group: External Consultation
    {
        "requirement_key": "external_consultation",
        "requirement_title": "External Consultation",
        "group_order": 12,
        "questions": [
            {
                "question_key": "cpra_12_1",
                "question_text": "Were external parties consulted in preparing this assessment?",
                "guidance": "Per CPPA regulations, document whether external experts (including AI bias detection experts) were consulted.",
                "question_order": 1,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
            {
                "question_key": "cpra_12_2",
                "question_text": "If external parties were not consulted, explain why.",
                "guidance": "Provide justification for not seeking external expertise, particularly for ADMT processing.",
                "question_order": 2,
                "required": False,
                "fides_sources": [],
                "expected_coverage": "none",
            },
        ],
    },
    # New Group: Negative Impacts Detail
    {
        "requirement_key": "negative_impacts_detail",
        "requirement_title": "Detailed Negative Impact Analysis",
        "group_order": 13,
        "questions": [
            {
                "question_key": "cpra_13_1",
                "question_text": "Could this processing result in unauthorized access to or loss of availability of personal information?",
                "guidance": "Assess security-related negative impacts to consumers.",
                "question_order": 1,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
            {
                "question_key": "cpra_13_2",
                "question_text": "Could this processing result in unlawful discrimination against consumers?",
                "guidance": "Assess whether the processing could lead to discriminatory outcomes based on protected characteristics.",
                "question_order": 2,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
            {
                "question_key": "cpra_13_3",
                "question_text": "Could this processing result in consumer coercion or use of dark patterns?",
                "guidance": "Assess whether the processing design could manipulate or coerce consumers into sharing more data or making choices against their interests.",
                "question_order": 3,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
            {
                "question_key": "cpra_13_4",
                "question_text": "Could this processing result in loss of consumer control over their personal information?",
                "guidance": "Assess impacts on consumer autonomy and ability to manage their data.",
                "question_order": 4,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
        ],
    },
]


def upgrade() -> None:
    conn = op.get_bind()
    now = datetime.now(timezone.utc)

    # Add questions to GDPR DPIA template
    result = conn.execute(
        sa.text("SELECT id FROM assessment_template WHERE key = 'gdpr_dpia'")
    )
    row = result.fetchone()

    if row:
        template_id = row[0]
        question_count = 0

        for group in GDPR_DPIA_ADDITIONAL_QUESTIONS:
            for question in group["questions"]:
                # Check if question already exists
                existing = conn.execute(
                    sa.text(
                        "SELECT id FROM assessment_question WHERE template_id = :template_id AND question_key = :question_key"
                    ),
                    {"template_id": template_id, "question_key": question["question_key"]},
                )
                if existing.fetchone():
                    print(f"Question {question['question_key']} already exists, skipping")
                    continue

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
                question_count += 1

        print(f"Added {question_count} questions to GDPR DPIA template")
    else:
        print("GDPR DPIA template not found")

    # Add questions to California CPRA template
    result = conn.execute(
        sa.text("SELECT id FROM assessment_template WHERE key = 'us_ca_cpra_risk_assessment'")
    )
    row = result.fetchone()

    if row:
        template_id = row[0]
        question_count = 0

        for group in CPRA_ADDITIONAL_QUESTIONS:
            for question in group["questions"]:
                # Check if question already exists
                existing = conn.execute(
                    sa.text(
                        "SELECT id FROM assessment_question WHERE template_id = :template_id AND question_key = :question_key"
                    ),
                    {"template_id": template_id, "question_key": question["question_key"]},
                )
                if existing.fetchone():
                    print(f"Question {question['question_key']} already exists, skipping")
                    continue

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
                question_count += 1

        print(f"Added {question_count} questions to California CPRA template")
    else:
        print("California CPRA template not found")


def downgrade() -> None:
    conn = op.get_bind()

    # Remove added GDPR DPIA questions
    gdpr_question_keys = [
        "dpia_7_3", "dpia_8_1", "dpia_8_2", "dpia_9_1", "dpia_9_2"
    ]
    for key in gdpr_question_keys:
        conn.execute(
            sa.text("DELETE FROM assessment_question WHERE question_key = :key"),
            {"key": key},
        )
    print(f"Removed {len(gdpr_question_keys)} GDPR DPIA questions")

    # Remove added CPRA questions
    cpra_question_keys = [
        "cpra_11_1", "cpra_11_2", "cpra_12_1", "cpra_12_2",
        "cpra_13_1", "cpra_13_2", "cpra_13_3", "cpra_13_4"
    ]
    for key in cpra_question_keys:
        conn.execute(
            sa.text("DELETE FROM assessment_question WHERE question_key = :key"),
            {"key": key},
        )
    print(f"Removed {len(cpra_question_keys)} CPRA questions")
