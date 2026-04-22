"""add California CPRA 2025 assessment template

Deactivates the previous California CPRA risk assessment template and seeds
the updated v2025 template with 47 questions across 16 sections.

Revision ID: b075e9f80d20
Revises: f7a8b9c0d1e2
Create Date: 2026-04-17 11:00:00.000000

"""

import uuid
from datetime import datetime, timezone

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "b075e9f80d20"
down_revision = "f7a8b9c0d1e2"
branch_labels = None
depends_on = None


def generate_id(prefix: str) -> str:
    """Generate a prefixed UUID."""
    return f"{prefix}_{uuid.uuid4()}"


ASSESSMENT_TEMPLATE = {
    "assessment_type": "us_ca_cpra_risk_assessment",
    "version": "US-CA-CPPA-RA-2025-09-23",
    "fides_revision": 1,
    "name": "California CPRA / CCPA Risk Assessment",
    "region": "United States (California)",
    "authority": "California Privacy Protection Agency",
    "legal_reference": (
        "CCPA Regulations (Title 11, Division 6, Chapter 1, Article 10),"
        " final text approved by OAL 22 September 2025; compliance required"
        " from 1 January 2026"
    ),
    "description": (
        "Risk assessment for processing that presents significant risk to"
        " consumers' privacy. Reflects the final CPPA rules on risk"
        " assessments, ADMT, and cybersecurity audits approved by the"
        " California Office of Administrative Law on 22 September 2025."
    ),
    "is_active": True,
    "is_managed": True,
}

TEMPLATE_QUESTIONS = [
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
                "guidance": (
                    "State the purposes in concrete terms, not generic"
                    " descriptions. \"Business purposes\" is not sufficient"
                    " \u2014 describe the precise objective (e.g., \"provide"
                    " personalized product recommendations based on browsing"
                    " history and purchase patterns\")."
                ),
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
                "fides_sources": [
                    "privacy_declaration.data_use",
                    "data_use.name",
                ],
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
                "question_text": "Does this processing use automated decision-making technology (ADMT) for significant decisions?",
                "guidance": (
                    "\"Significant decisions\" include those producing legal"
                    " or similarly significant effects on consumers (e.g.,"
                    " financial, lending, housing, insurance, education,"
                    " employment, healthcare access)."
                ),
                "question_order": 4,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
            {
                "question_key": "cpra_2_5",
                "question_text": "Does this processing train ADMT for identification, trait inference, emotion analysis, or facial/biometric recognition?",
                "guidance": "Training activities that fall within this trigger require a risk assessment regardless of whether the ADMT is used in production decisions.",
                "question_order": 5,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
            {
                "question_key": "cpra_2_6",
                "question_text": "Does this processing use automated inference to derive traits related to employment, education, or sensitive locations?",
                "guidance": "Examples include performance scoring from workplace monitoring, academic risk scoring, or location-based profiling.",
                "question_order": 6,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
            {
                "question_key": "cpra_2_7",
                "question_text": "Does this processing involve systematic observation of consumers acting in an educational, employment, or contractor capacity?",
                "guidance": (
                    "Systematic observation includes Wi-Fi/Bluetooth tracking,"
                    " RFID, drones, video/audio recording or livestreaming,"
                    " geofencing, location trackers, and license-plate"
                    " recognition used to profile applicants, students,"
                    " employees, or independent contractors."
                ),
                "question_order": 7,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
        ],
    },
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
                "fides_sources": [
                    "privacy_notice.name",
                    "privacy_notice.data_uses",
                ],
                "expected_coverage": "full",
            },
            {
                "question_key": "cpra_4_2",
                "question_text": "Are just-in-time notices provided at collection points?",
                "guidance": "Document any point-of-collection notices beyond the privacy policy.",
                "question_order": 2,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
        ],
    },
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
                "fides_sources": [
                    "privacy_experience",
                    "policy.drp_action",
                ],
                "expected_coverage": "partial",
            },
        ],
    },
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
                "question_text": "What are the benefits to other stakeholders and the public?",
                "guidance": "Describe broader societal benefits beyond the direct parties.",
                "question_order": 3,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
            {
                "question_key": "cpra_10_4",
                "question_text": "What are the potential negative impacts on consumers?",
                "guidance": "Identify privacy risks, potential harms, and other negative impacts.",
                "question_order": 4,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
            {
                "question_key": "cpra_10_5",
                "question_text": "Do the benefits outweigh the risks, as mitigated by the safeguards documented in this assessment?",
                "guidance": (
                    "Provide a balanced assessment of benefits vs. risks."
                    " The final CPPA rules state that the goal of a risk"
                    " assessment is to restrict or prohibit processing"
                    " activities whose risks to privacy outweigh the benefits."
                ),
                "question_order": 5,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
            {
                "question_key": "cpra_10_6",
                "question_text": "Will the business proceed with the processing?",
                "guidance": (
                    "State explicitly whether the processing will go forward,"
                    " proceed with additional safeguards, or be"
                    " restricted/halted. This is a substantive decision, not"
                    " just a documentation exercise."
                ),
                "question_order": 6,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
        ],
    },
    {
        "requirement_key": "admt_details",
        "requirement_title": "Automated Decision-Making Technology Details",
        "group_order": 11,
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
    {
        "requirement_key": "stakeholder_involvement",
        "requirement_title": "Stakeholder Involvement and External Consultation",
        "group_order": 12,
        "questions": [
            {
                "question_key": "cpra_12_1",
                "question_text": "Which internal stakeholders provided information for or contributed to this assessment?",
                "guidance": (
                    "Identify the individuals and teams involved in the"
                    " processing activity who contributed to the assessment"
                    " (e.g., product, engineering, security, data science,"
                    " HR). Legal counsel should be excluded from this list to"
                    " preserve attorney-client privilege."
                ),
                "question_order": 1,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
            {
                "question_key": "cpra_12_2",
                "question_text": "Were external parties consulted in preparing this assessment?",
                "guidance": "Document whether external experts (including AI bias detection experts, affected consumer representatives, or academic reviewers) were consulted.",
                "question_order": 2,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
            {
                "question_key": "cpra_12_3",
                "question_text": "If external parties were not consulted, explain why.",
                "guidance": "Provide justification for not seeking external expertise, particularly for ADMT processing.",
                "question_order": 3,
                "required": False,
                "fides_sources": [],
                "expected_coverage": "none",
            },
        ],
    },
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
    {
        "requirement_key": "review_approval",
        "requirement_title": "Review and Approval",
        "group_order": 14,
        "questions": [
            {
                "question_key": "cpra_14_1",
                "question_text": "Who is the executive management team member responsible for compliance with this assessment?",
                "guidance": (
                    "Identify the named executive with ultimate"
                    " accountability. The final CPPA rules require businesses"
                    " to identify the executive management team member"
                    " responsible for the assessment's compliance."
                ),
                "question_order": 1,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
            {
                "question_key": "cpra_14_2",
                "question_text": "Names, positions, and sign-off dates of reviewers and approvers.",
                "guidance": (
                    "Document everyone who reviewed and approved the"
                    " assessment, along with the date of approval. Exclude"
                    " legal counsel from this list to preserve privilege."
                ),
                "question_order": 2,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
            {
                "question_key": "cpra_14_3",
                "question_text": "What is the date this assessment was completed?",
                "guidance": (
                    "Risk assessments must be conducted before initiating the"
                    " processing activity (or, for activities underway before"
                    " 1 January 2026, completed by 31 December 2027)."
                ),
                "question_order": 3,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
        ],
    },
    {
        "requirement_key": "review_cadence",
        "requirement_title": "Review Cadence and Change Management",
        "group_order": 15,
        "questions": [
            {
                "question_key": "cpra_15_1",
                "question_text": "When will this assessment next be reviewed?",
                "guidance": "Assessments must be reviewed at least every three years. Document the scheduled next-review date.",
                "question_order": 1,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
            {
                "question_key": "cpra_15_2",
                "question_text": "What material changes would trigger an earlier reassessment?",
                "guidance": (
                    "Material changes to the processing activity require a"
                    " re-review as soon as feasibly possible, and no later"
                    " than 45 calendar days after the change. Identify"
                    " specific triggers such as new data categories, new"
                    " purposes, new ADMT use, new third-party recipients, or"
                    " changes in consumer populations."
                ),
                "question_order": 2,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
        ],
    },
    {
        "requirement_key": "cppa_submission",
        "requirement_title": "CPPA Submission Packet",
        "group_order": 16,
        "questions": [
            {
                "question_key": "cpra_16_1",
                "question_text": "Point of contact for this assessment.",
                "guidance": "Name, role, and contact details of the individual the CPPA should contact regarding this assessment.",
                "question_order": 1,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
            {
                "question_key": "cpra_16_2",
                "question_text": "Time period covered by this assessment.",
                "guidance": "Start and end dates of the assessment window being reported.",
                "question_order": 2,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
            {
                "question_key": "cpra_16_3",
                "question_text": "Categories of personal information and sensitive personal information covered.",
                "guidance": "List the PI and SPI categories addressed in this assessment for inclusion in the annual CPPA submission.",
                "question_order": 3,
                "required": True,
                "fides_sources": [
                    "privacy_declaration.data_categories",
                    "data_category.name",
                ],
                "expected_coverage": "full",
            },
            {
                "question_key": "cpra_16_4",
                "question_text": "Attestation.",
                "guidance": (
                    "The business must attest, under penalty of perjury, that"
                    " the risk assessment was conducted in accordance with the"
                    " CCPA regulations. Record the name and position of the"
                    " individual signing the attestation."
                ),
                "question_order": 4,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
            {
                "question_key": "cpra_16_5",
                "question_text": "Submission schedule.",
                "guidance": (
                    "For assessments conducted in 2026 and 2027, submit to the"
                    " CPPA by 1 April 2028. For assessments conducted after"
                    " 2027, submit by 1 April of the year following the"
                    " assessment. The CPPA or Attorney General may also"
                    " request a full copy of the assessment within 30 calendar"
                    " days of the request."
                ),
                "question_order": 5,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
        ],
    },
]

# Old template version for downgrade re-activation
OLD_TEMPLATE_VERSION = "US-CA-CPPA-RA-2024-03-29"


def _format_fides_sources(sources: list[str]) -> str:
    """Format a list of fides_sources as a PostgreSQL array literal."""
    if not sources:
        return "{}"
    return "{" + ",".join(sources) + "}"


def upgrade() -> None:
    conn = op.get_bind()
    now = datetime.now(timezone.utc)

    # Step 1: Deactivate the old CPRA template
    conn.execute(
        sa.text(
            "UPDATE assessment_template SET is_active = false"
            " WHERE assessment_type = 'us_ca_cpra_risk_assessment'"
            " AND is_active = true"
        ),
    )
    print("Deactivated old us_ca_cpra_risk_assessment template(s)")

    # Step 2: Check if the new template already exists (idempotency)
    result = conn.execute(
        sa.text(
            "SELECT id FROM assessment_template"
            " WHERE assessment_type = :assessment_type"
            " AND version = :version"
            " AND fides_revision = :fides_revision"
        ),
        {
            "assessment_type": ASSESSMENT_TEMPLATE["assessment_type"],
            "version": ASSESSMENT_TEMPLATE["version"],
            "fides_revision": ASSESSMENT_TEMPLATE["fides_revision"],
        },
    )
    row = result.fetchone()

    if row:
        print(
            f"Template {ASSESSMENT_TEMPLATE['assessment_type']}"
            f" v{ASSESSMENT_TEMPLATE['version']} already exists, skipping"
        )
        template_id = row[0]
    else:
        template_id = generate_id("ast")
        conn.execute(
            sa.text("""
                INSERT INTO assessment_template
                    (id, version, name, assessment_type, region, authority,
                     legal_reference, description, is_active, fides_revision,
                     is_managed, created_at, updated_at)
                VALUES
                    (:id, :version, :name, :assessment_type, :region, :authority,
                     :legal_reference, :description, :is_active, :fides_revision,
                     :is_managed, :created_at, :updated_at)
            """),
            {
                "id": template_id,
                "version": ASSESSMENT_TEMPLATE["version"],
                "name": ASSESSMENT_TEMPLATE["name"],
                "assessment_type": ASSESSMENT_TEMPLATE["assessment_type"],
                "region": ASSESSMENT_TEMPLATE["region"],
                "authority": ASSESSMENT_TEMPLATE["authority"],
                "legal_reference": ASSESSMENT_TEMPLATE["legal_reference"],
                "description": ASSESSMENT_TEMPLATE["description"],
                "is_active": ASSESSMENT_TEMPLATE["is_active"],
                "fides_revision": ASSESSMENT_TEMPLATE["fides_revision"],
                "is_managed": ASSESSMENT_TEMPLATE["is_managed"],
                "created_at": now,
                "updated_at": now,
            },
        )
        print(
            f"Created template: {ASSESSMENT_TEMPLATE['assessment_type']}"
            f" v{ASSESSMENT_TEMPLATE['version']}"
        )

    # Step 3: Check if questions already exist
    result = conn.execute(
        sa.text(
            "SELECT COUNT(*) FROM assessment_question"
            " WHERE template_id = :template_id"
        ),
        {"template_id": template_id},
    )
    count = result.fetchone()[0]
    if count > 0:
        print(
            f"Template {ASSESSMENT_TEMPLATE['assessment_type']} already has"
            f" {count} questions, skipping"
        )
        return

    # Step 4: Seed questions
    question_count = 0
    for group in TEMPLATE_QUESTIONS:
        for question in group["questions"]:
            question_id = generate_id("asq")
            conn.execute(
                sa.text("""
                    INSERT INTO assessment_question
                        (id, template_id, requirement_key, requirement_title,
                         group_order, question_key, question_text, guidance,
                         question_order, required, fides_sources,
                         expected_coverage, created_at, updated_at)
                    VALUES
                        (:id, :template_id, :requirement_key, :requirement_title,
                         :group_order, :question_key, :question_text, :guidance,
                         :question_order, :required, :fides_sources,
                         :expected_coverage, :created_at, :updated_at)
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
                    "fides_sources": _format_fides_sources(
                        question["fides_sources"]
                    ),
                    "expected_coverage": question["expected_coverage"],
                    "created_at": now,
                    "updated_at": now,
                },
            )
            question_count += 1

    print(
        f"Seeded {question_count} questions for"
        f" {ASSESSMENT_TEMPLATE['assessment_type']}"
    )


def downgrade() -> None:
    conn = op.get_bind()

    # Step 1: Find and delete the new template + its questions
    result = conn.execute(
        sa.text(
            "SELECT id FROM assessment_template"
            " WHERE assessment_type = :assessment_type"
            " AND version = :version"
            " AND fides_revision = :fides_revision"
        ),
        {
            "assessment_type": ASSESSMENT_TEMPLATE["assessment_type"],
            "version": ASSESSMENT_TEMPLATE["version"],
            "fides_revision": ASSESSMENT_TEMPLATE["fides_revision"],
        },
    )
    row = result.fetchone()

    if row:
        template_id = row[0]
        conn.execute(
            sa.text(
                "DELETE FROM assessment_question"
                " WHERE template_id = :template_id"
            ),
            {"template_id": template_id},
        )
        conn.execute(
            sa.text("DELETE FROM assessment_template WHERE id = :id"),
            {"id": template_id},
        )
        print(
            f"Deleted template: {ASSESSMENT_TEMPLATE['assessment_type']}"
            f" v{ASSESSMENT_TEMPLATE['version']}"
        )

    # Step 2: Re-activate the old template
    conn.execute(
        sa.text(
            "UPDATE assessment_template SET is_active = true"
            " WHERE assessment_type = 'us_ca_cpra_risk_assessment'"
            " AND version = :old_version"
        ),
        {"old_version": OLD_TEMPLATE_VERSION},
    )
    print(
        f"Re-activated old us_ca_cpra_risk_assessment template"
        f" v{OLD_TEMPLATE_VERSION}"
    )
