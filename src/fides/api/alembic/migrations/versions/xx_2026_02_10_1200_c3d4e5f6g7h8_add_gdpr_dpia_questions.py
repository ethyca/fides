"""add GDPR DPIA questions

Revision ID: c3d4e5f6g7h8
Revises: 4d64174f422e
Create Date: 2026-02-10 12:00:00.000000

"""

import uuid
from datetime import datetime, timezone

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "c3d4e5f6g7h8"
down_revision = "4d64174f422e"
branch_labels = None
depends_on = None


def generate_id(prefix: str) -> str:
    """Generate a prefixed UUID."""
    return f"{prefix}_{uuid.uuid4()}"


# GDPR DPIA Questions organized by requirement group (per Article 35)
GDPR_DPIA_QUESTIONS = [
    # Group 1: Description of Processing Operations
    {
        "requirement_key": "processing_description",
        "requirement_title": "Description of Processing Operations",
        "group_order": 1,
        "questions": [
            {
                "question_key": "dpia_1_1",
                "question_text": "Describe the nature, scope, context and purposes of the processing.",
                "guidance": "Provide a systematic description of the envisaged processing operations.",
                "question_order": 1,
                "required": True,
                "fides_sources": [
                    "system.name",
                    "system.description",
                    "privacy_declaration.name",
                    "privacy_declaration.data_use",
                ],
                "expected_coverage": "partial",
            },
            {
                "question_key": "dpia_1_2",
                "question_text": "What categories of personal data are processed?",
                "guidance": "List all categories of personal data involved in the processing.",
                "question_order": 2,
                "required": True,
                "fides_sources": [
                    "privacy_declaration.data_categories",
                    "data_category.name",
                ],
                "expected_coverage": "full",
            },
            {
                "question_key": "dpia_1_3",
                "question_text": "What categories of data subjects are affected?",
                "guidance": "Identify the individuals whose data is processed (employees, customers, etc.).",
                "question_order": 3,
                "required": True,
                "fides_sources": ["privacy_declaration.data_subjects"],
                "expected_coverage": "full",
            },
            {
                "question_key": "dpia_1_4",
                "question_text": "What is the data retention period?",
                "guidance": "Specify how long the data will be retained or the criteria for determining retention.",
                "question_order": 4,
                "required": True,
                "fides_sources": ["privacy_declaration.retention_period"],
                "expected_coverage": "partial",
            },
        ],
    },
    # Group 2: Necessity and Proportionality
    {
        "requirement_key": "necessity_proportionality",
        "requirement_title": "Necessity and Proportionality",
        "group_order": 2,
        "questions": [
            {
                "question_key": "dpia_2_1",
                "question_text": "What is the lawful basis for processing under Article 6?",
                "guidance": "Identify the legal basis (consent, contract, legal obligation, vital interests, public task, legitimate interests).",
                "question_order": 1,
                "required": True,
                "fides_sources": ["privacy_declaration.legal_basis_for_processing"],
                "expected_coverage": "full",
            },
            {
                "question_key": "dpia_2_2",
                "question_text": "How is the processing necessary for the stated purpose?",
                "guidance": "Explain why this processing is necessary and proportionate to achieve the purpose.",
                "question_order": 2,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
            {
                "question_key": "dpia_2_3",
                "question_text": "Could the purpose be achieved with less data or less intrusive processing?",
                "guidance": "Consider data minimisation - is all collected data necessary?",
                "question_order": 3,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
        ],
    },
    # Group 3: Risk Assessment
    {
        "requirement_key": "risk_assessment",
        "requirement_title": "Risk Assessment",
        "group_order": 3,
        "questions": [
            {
                "question_key": "dpia_3_1",
                "question_text": "What risks does this processing pose to the rights and freedoms of data subjects?",
                "guidance": "Identify potential physical, material or non-material damage (discrimination, identity theft, financial loss, reputational damage, etc.).",
                "question_order": 1,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
            {
                "question_key": "dpia_3_2",
                "question_text": "What is the likelihood and severity of each identified risk?",
                "guidance": "Assess the probability and potential impact of each risk materialising.",
                "question_order": 2,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
            {
                "question_key": "dpia_3_3",
                "question_text": "Does the processing involve special categories of data (Article 9)?",
                "guidance": "Special categories include health, genetic, biometric, racial/ethnic origin, political opinions, religious beliefs, trade union membership, sex life/orientation.",
                "question_order": 3,
                "required": True,
                "fides_sources": ["privacy_declaration.data_categories"],
                "expected_coverage": "full",
            },
        ],
    },
    # Group 4: Risk Mitigation Measures
    {
        "requirement_key": "risk_mitigation",
        "requirement_title": "Risk Mitigation Measures",
        "group_order": 4,
        "questions": [
            {
                "question_key": "dpia_4_1",
                "question_text": "What technical measures are in place to protect personal data?",
                "guidance": "Describe encryption, pseudonymisation, access controls, security monitoring, etc.",
                "question_order": 1,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
            {
                "question_key": "dpia_4_2",
                "question_text": "What organisational measures are in place?",
                "guidance": "Describe policies, staff training, access management, audit procedures, etc.",
                "question_order": 2,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
            {
                "question_key": "dpia_4_3",
                "question_text": "How are the identified risks mitigated by these measures?",
                "guidance": "Map each risk to the specific measures that address it.",
                "question_order": 3,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
        ],
    },
    # Group 5: Data Subject Rights
    {
        "requirement_key": "data_subject_rights",
        "requirement_title": "Data Subject Rights",
        "group_order": 5,
        "questions": [
            {
                "question_key": "dpia_5_1",
                "question_text": "How are data subjects informed about the processing (Articles 13/14)?",
                "guidance": "Describe the privacy notice or information provided to data subjects.",
                "question_order": 1,
                "required": True,
                "fides_sources": ["privacy_notice.name", "privacy_notice.data_uses"],
                "expected_coverage": "partial",
            },
            {
                "question_key": "dpia_5_2",
                "question_text": "How can data subjects exercise their rights (access, rectification, erasure, etc.)?",
                "guidance": "Describe the mechanisms for handling data subject requests.",
                "question_order": 2,
                "required": True,
                "fides_sources": ["privacy_experience", "policy.drp_action"],
                "expected_coverage": "partial",
            },
        ],
    },
    # Group 6: Third-Party Sharing
    {
        "requirement_key": "third_party_sharing",
        "requirement_title": "Third-Party Sharing and Transfers",
        "group_order": 6,
        "questions": [
            {
                "question_key": "dpia_6_1",
                "question_text": "With which third parties is personal data shared?",
                "guidance": "List all recipients including processors, joint controllers, and other third parties.",
                "question_order": 1,
                "required": True,
                "fides_sources": [
                    "privacy_declaration.third_parties",
                    "connection.name",
                ],
                "expected_coverage": "partial",
            },
            {
                "question_key": "dpia_6_2",
                "question_text": "Are there any international transfers outside the EEA?",
                "guidance": "If yes, identify the countries and the transfer mechanism (adequacy, SCCs, BCRs, etc.).",
                "question_order": 2,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
        ],
    },
    # Group 7: Consultation
    {
        "requirement_key": "consultation",
        "requirement_title": "Consultation and Prior Consultation",
        "group_order": 7,
        "questions": [
            {
                "question_key": "dpia_7_1",
                "question_text": "Have data subjects or their representatives been consulted?",
                "guidance": "If appropriate, describe any consultation with affected individuals.",
                "question_order": 1,
                "required": False,
                "fides_sources": [],
                "expected_coverage": "none",
            },
            {
                "question_key": "dpia_7_2",
                "question_text": "Is prior consultation with the supervisory authority required (Article 36)?",
                "guidance": "Required if the DPIA indicates high residual risk that cannot be mitigated.",
                "question_order": 2,
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

    # Find the GDPR DPIA template
    result = conn.execute(
        sa.text("SELECT id FROM assessment_template WHERE key = 'gdpr_dpia'")
    )
    row = result.fetchone()

    if not row:
        print("GDPR DPIA template not found, skipping question seeding")
        return

    template_id = row[0]
    print(f"Found GDPR DPIA template: {template_id}")

    # Check if questions already exist
    result = conn.execute(
        sa.text(
            "SELECT COUNT(*) FROM assessment_question WHERE template_id = :template_id"
        ),
        {"template_id": template_id},
    )
    count = result.fetchone()[0]
    if count > 0:
        print(f"GDPR DPIA template already has {count} questions, skipping")
        return

    # Seed GDPR DPIA questions
    question_count = 0
    for group in GDPR_DPIA_QUESTIONS:
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
            question_count += 1

    print(f"Seeded {question_count} GDPR DPIA questions")


def downgrade() -> None:
    conn = op.get_bind()

    # Find the GDPR DPIA template
    result = conn.execute(
        sa.text("SELECT id FROM assessment_template WHERE key = 'gdpr_dpia'")
    )
    row = result.fetchone()

    if row:
        template_id = row[0]
        conn.execute(
            sa.text("DELETE FROM assessment_question WHERE template_id = :template_id"),
            {"template_id": template_id},
        )
        print(f"Deleted GDPR DPIA questions for template {template_id}")
