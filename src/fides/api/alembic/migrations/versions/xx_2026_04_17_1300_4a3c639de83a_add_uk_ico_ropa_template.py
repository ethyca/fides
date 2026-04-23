"""Add UK ICO ROPA assessment template

Seeds the assessment_template and assessment_question tables with the
UK ICO Record of Processing Activities (ROPA) template.

Revision ID: 4a3c639de83a
Revises: 17e350c9f4c4
Create Date: 2026-04-17 13:00:00.000000

"""

import uuid
from datetime import datetime, timezone

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "4a3c639de83a"
down_revision = "17e350c9f4c4"
branch_labels = None
depends_on = None


def generate_id(prefix: str) -> str:
    """Generate a prefixed UUID."""
    return f"{prefix}_{uuid.uuid4()}"


ASSESSMENT_TEMPLATE = {
    "assessment_type": "uk_ico_ropa",
    "version": "UK-ICO-ROPA-2024",
    "fides_revision": 1,
    "name": "UK ICO Record of Processing Activities (ROPA)",
    "region": "United Kingdom",
    "authority": "Information Commissioner's Office (ICO)",
    "legal_reference": "UK GDPR Article 30, Data Protection Act 2018, ICO Documentation Guidance",
    "description": "Record of processing activities maintained by controllers and processors under UK GDPR Article 30. Fields marked as required are required by Article 30; optional fields are recommended by the ICO to support wider accountability obligations under Article 5(2).",
    "is_active": True,
    "is_managed": True,
}

TEMPLATE_QUESTIONS = [
    {
        "requirement_key": "controller_identification",
        "requirement_title": "Controller Identification (Art 30(1)(a))",
        "group_order": 1,
        "questions": [
            {
                "question_key": "ico_1_1",
                "question_text": "What is the legal name of the controller?",
                "guidance": "The full legal name of the organisation acting as controller for this processing activity.",
                "question_order": 1,
                "required": True,
                "fides_sources": "{}",
                "expected_coverage": "none",
            },
            {
                "question_key": "ico_1_2",
                "question_text": "What are the contact details of the controller?",
                "guidance": "Registered address and contact details sufficient for data subjects and the ICO to reach the controller.",
                "question_order": 2,
                "required": True,
                "fides_sources": "{}",
                "expected_coverage": "none",
            },
            {
                "question_key": "ico_1_3",
                "question_text": "If this is a joint controller arrangement, who are the joint controllers and what are their respective responsibilities?",
                "guidance": "Identify all joint controllers and summarise the essence of the arrangement under Article 26, including who is the point of contact for data subjects.",
                "question_order": 3,
                "required": True,
                "fides_sources": "{}",
                "expected_coverage": "none",
            },
            {
                "question_key": "ico_1_4",
                "question_text": "Who is the Data Protection Officer (DPO) and how can they be contacted?",
                "guidance": "Name and contact details of the DPO where one is appointed. If no DPO is appointed, document the decision and the role responsible for privacy oversight.",
                "question_order": 4,
                "required": True,
                "fides_sources": "{}",
                "expected_coverage": "none",
            },
            {
                "question_key": "ico_1_5",
                "question_text": "If the controller is not established in the UK, who is the UK Representative?",
                "guidance": "Where Article 27 applies, name the UK representative and their contact details. Leave blank only if the controller is UK-established or otherwise exempt.",
                "question_order": 5,
                "required": True,
                "fides_sources": "{}",
                "expected_coverage": "none",
            },
            {
                "question_key": "ico_1_6",
                "question_text": "Is this organisation acting as controller or processor for this activity?",
                "guidance": "Identify whether Article 30(1) (controller) or Article 30(2) (processor) obligations apply. Joint and independent controller scenarios should also be documented here.",
                "question_order": 6,
                "required": False,
                "fides_sources": "{}",
                "expected_coverage": "none",
            },
            {
                "question_key": "ico_1_7",
                "question_text": "Which department is responsible for this processing activity?",
                "guidance": "The internal team or business function that owns the processing.",
                "question_order": 7,
                "required": False,
                "fides_sources": "{system.administrating_department}",
                "expected_coverage": "partial",
            },
            {
                "question_key": "ico_1_8",
                "question_text": "Who are the designated data stewards for this processing?",
                "guidance": "Named individuals accountable for the day-to-day management of the data.",
                "question_order": 8,
                "required": False,
                "fides_sources": "{system.data_stewards}",
                "expected_coverage": "partial",
            },
        ],
    },
    {
        "requirement_key": "processing_purposes",
        "requirement_title": "Processing Operation and Purposes (Art 30(1)(b))",
        "group_order": 2,
        "questions": [
            {
                "question_key": "ico_2_1",
                "question_text": "What are the purposes of the processing?",
                "guidance": "State the specific purposes for which personal data is processed. Avoid generic descriptions such as \"business operations\" -- purposes should be sufficiently detailed for a data subject to understand why their data is being used.",
                "question_order": 1,
                "required": True,
                "fides_sources": "{privacy_declaration.data_use,data_use.name,data_use.description}",
                "expected_coverage": "full",
            },
            {
                "question_key": "ico_2_2",
                "question_text": "Provide a description of the system or processing activity.",
                "guidance": "A short narrative description of the system, service, or workflow that implements this processing.",
                "question_order": 2,
                "required": False,
                "fides_sources": "{system.name,system.description,privacy_declaration.name}",
                "expected_coverage": "partial",
            },
        ],
    },
    {
        "requirement_key": "data_subjects_personal_data",
        "requirement_title": "Data Subjects and Personal Data (Art 30(1)(c))",
        "group_order": 3,
        "questions": [
            {
                "question_key": "ico_3_1",
                "question_text": "What categories of individuals are affected by this processing?",
                "guidance": "Categories of data subjects (e.g., customers, employees, job applicants, website visitors, children).",
                "question_order": 1,
                "required": True,
                "fides_sources": "{privacy_declaration.data_subjects}",
                "expected_coverage": "full",
            },
            {
                "question_key": "ico_3_2",
                "question_text": "What categories of personal data are processed?",
                "guidance": "List all categories of personal data. Where a taxonomy is used internally, ensure the categories are also understandable in plain English for ICO inspection purposes.",
                "question_order": 2,
                "required": True,
                "fides_sources": "{privacy_declaration.data_categories,data_category.name}",
                "expected_coverage": "full",
            },
            {
                "question_key": "ico_3_3",
                "question_text": "Does this processing involve special category data under Article 9 or criminal offence data under Article 10?",
                "guidance": "Flag whether special category or criminal offence data is processed. This triggers additional conditions under Article 9(2), Article 10, and DPA 2018 Schedule 1.",
                "question_order": 3,
                "required": False,
                "fides_sources": "{privacy_declaration.data_categories}",
                "expected_coverage": "partial",
            },
            {
                "question_key": "ico_3_4",
                "question_text": "What is the source of the personal data?",
                "guidance": "Identify whether data is collected directly from the data subject or obtained from a third party (and if so, which). Required indirectly to satisfy Article 14 transparency obligations.",
                "question_order": 4,
                "required": False,
                "fides_sources": "{}",
                "expected_coverage": "none",
            },
        ],
    },
    {
        "requirement_key": "recipients_sharing",
        "requirement_title": "Recipients and Data Sharing (Art 30(1)(d))",
        "group_order": 4,
        "questions": [
            {
                "question_key": "ico_4_1",
                "question_text": "What categories of recipients receive the personal data?",
                "guidance": "List all recipients including internal teams, processors, joint controllers, and other third parties.",
                "question_order": 1,
                "required": True,
                "fides_sources": "{privacy_declaration.third_parties,connection.name}",
                "expected_coverage": "partial",
            },
            {
                "question_key": "ico_4_2",
                "question_text": "Is personal data shared with third parties?",
                "guidance": "A boolean flag complementing the recipients field above. Helps quickly identify sharing activities across the ROPA.",
                "question_order": 2,
                "required": True,
                "fides_sources": "{privacy_declaration.third_parties}",
                "expected_coverage": "partial",
            },
        ],
    },
    {
        "requirement_key": "international_transfers",
        "requirement_title": "International Transfers (Art 30(1)(e))",
        "group_order": 5,
        "questions": [
            {
                "question_key": "ico_5_1",
                "question_text": "Are there any transfers of personal data to third countries or international organisations?",
                "guidance": "Identify all destination countries or international organisations outside the UK, and the data categories involved in each transfer.",
                "question_order": 1,
                "required": True,
                "fides_sources": "{}",
                "expected_coverage": "none",
            },
            {
                "question_key": "ico_5_2",
                "question_text": "What safeguards are in place for these transfers?",
                "guidance": "Document the transfer mechanism -- UK adequacy decision, International Data Transfer Agreement (IDTA), UK Addendum to the EU SCCs, Binding Corporate Rules, or an Article 49 derogation. Attach or link to the relevant instrument.",
                "question_order": 2,
                "required": True,
                "fides_sources": "{}",
                "expected_coverage": "none",
            },
        ],
    },
    {
        "requirement_key": "retention_erasure",
        "requirement_title": "Retention and Erasure (Art 30(1)(f))",
        "group_order": 6,
        "questions": [
            {
                "question_key": "ico_6_1",
                "question_text": "What are the retention periods for each category of personal data?",
                "guidance": "State specific retention periods or the criteria used to determine them. Avoid generic statements such as \"as long as necessary\" without supporting criteria.",
                "question_order": 1,
                "required": True,
                "fides_sources": "{privacy_declaration.retention_period}",
                "expected_coverage": "partial",
            },
            {
                "question_key": "ico_6_2",
                "question_text": "Link to the retention and erasure policy.",
                "guidance": "Reference to the organisation's retention and erasure policy that governs this processing.",
                "question_order": 2,
                "required": False,
                "fides_sources": "{}",
                "expected_coverage": "none",
            },
            {
                "question_key": "ico_6_3",
                "question_text": "Is the processing in adherence with the retention policy?",
                "guidance": "Flag whether current retention aligns with the policy. Divergence should be documented and justified.",
                "question_order": 3,
                "required": False,
                "fides_sources": "{}",
                "expected_coverage": "none",
            },
            {
                "question_key": "ico_6_4",
                "question_text": "If not in adherence, what is the reason?",
                "guidance": "Document the business, legal, or technical reason for any deviation from the retention policy, and the remediation plan.",
                "question_order": 4,
                "required": False,
                "fides_sources": "{}",
                "expected_coverage": "none",
            },
        ],
    },
    {
        "requirement_key": "security_measures",
        "requirement_title": "Security Measures (Art 30(1)(g))",
        "group_order": 7,
        "questions": [
            {
                "question_key": "ico_7_1",
                "question_text": "What technical and organisational security measures are in place to protect the personal data?",
                "guidance": "Provide meaningful detail on encryption, access controls, logging, pseudonymisation, staff training, and procedural controls. \"Industry standard\" without elaboration is insufficient for ICO purposes.",
                "question_order": 1,
                "required": True,
                "fides_sources": "{}",
                "expected_coverage": "none",
            },
            {
                "question_key": "ico_7_2",
                "question_text": "Where is the personal data located (storage and processing locations)?",
                "guidance": "Document the physical and logical locations where data is stored and processed, including cloud regions.",
                "question_order": 2,
                "required": False,
                "fides_sources": "{}",
                "expected_coverage": "none",
            },
        ],
    },
    {
        "requirement_key": "lawful_basis",
        "requirement_title": "Lawful Basis and Special Categories (Arts 6, 9)",
        "group_order": 8,
        "questions": [
            {
                "question_key": "ico_8_1",
                "question_text": "What is the lawful basis for this processing under Article 6?",
                "guidance": "Identify the Article 6(1) lawful basis (consent, contract, legal obligation, vital interests, public task, legitimate interests). While not a strict Article 30 requirement, the ICO recommends documenting lawful basis to support Article 5(2) accountability.",
                "question_order": 1,
                "required": False,
                "fides_sources": "{privacy_declaration.legal_basis_for_processing}",
                "expected_coverage": "full",
            },
            {
                "question_key": "ico_8_2",
                "question_text": "If relying on legitimate interests under Article 6(1)(f), summarise the legitimate interests pursued.",
                "guidance": "Where legitimate interests is the lawful basis, document the specific interests being pursued by the controller or a third party.",
                "question_order": 2,
                "required": True,
                "fides_sources": "{}",
                "expected_coverage": "none",
            },
            {
                "question_key": "ico_8_3",
                "question_text": "Link to the Legitimate Interests Assessment (LIA).",
                "guidance": "Reference to the completed LIA demonstrating the balancing test between legitimate interests and data subject rights.",
                "question_order": 3,
                "required": True,
                "fides_sources": "{}",
                "expected_coverage": "none",
            },
            {
                "question_key": "ico_8_4",
                "question_text": "What Article 9 condition applies to the processing of special category data?",
                "guidance": "Identify the Article 9(2) condition (e.g., explicit consent, employment law, public health). Required where special category data is processed.",
                "question_order": 4,
                "required": False,
                "fides_sources": "{}",
                "expected_coverage": "none",
            },
            {
                "question_key": "ico_8_5",
                "question_text": "What DPA 2018 Schedule 1 condition applies?",
                "guidance": "For special category or criminal offence data processing in the UK, identify the specific Schedule 1 condition relied upon. Some Schedule 1 conditions additionally require an Appropriate Policy Document.",
                "question_order": 5,
                "required": True,
                "fides_sources": "{}",
                "expected_coverage": "none",
            },
        ],
    },
    {
        "requirement_key": "automated_decision_making",
        "requirement_title": "Automated Decision-Making and Profiling (Art 22)",
        "group_order": 9,
        "questions": [
            {
                "question_key": "ico_9_1",
                "question_text": "Does the processing involve profiling or solely automated decision-making?",
                "guidance": "Flag whether Article 22 is engaged. If so, additional transparency and data subject rights apply.",
                "question_order": 1,
                "required": False,
                "fides_sources": "{}",
                "expected_coverage": "none",
            },
            {
                "question_key": "ico_9_2",
                "question_text": "Describe the automated decision-making or profiling.",
                "guidance": "Describe the logic involved, the significance of the processing, and the envisaged consequences for the data subject.",
                "question_order": 2,
                "required": False,
                "fides_sources": "{}",
                "expected_coverage": "none",
            },
            {
                "question_key": "ico_9_3",
                "question_text": "What is the lawful basis for profiling or automated decision-making?",
                "guidance": "Article 22 requires one of: explicit consent, contractual necessity, or authorisation by UK law. Document the basis relied upon.",
                "question_order": 3,
                "required": False,
                "fides_sources": "{}",
                "expected_coverage": "none",
            },
        ],
    },
    {
        "requirement_key": "dpia",
        "requirement_title": "DPIA and Impact Assessments (Art 35)",
        "group_order": 10,
        "questions": [
            {
                "question_key": "ico_10_1",
                "question_text": "Is a Data Protection Impact Assessment (DPIA) required for this processing?",
                "guidance": "Determine whether Article 35 is triggered based on the ICO's list of processing types likely to result in high risk.",
                "question_order": 1,
                "required": False,
                "fides_sources": "{}",
                "expected_coverage": "none",
            },
            {
                "question_key": "ico_10_2",
                "question_text": "Where is the DPIA documented?",
                "guidance": "Link to the completed DPIA or explain why one is not required.",
                "question_order": 2,
                "required": False,
                "fides_sources": "{}",
                "expected_coverage": "none",
            },
        ],
    },
    {
        "requirement_key": "data_subject_rights",
        "requirement_title": "Data Subject Rights (Arts 12-22)",
        "group_order": 11,
        "questions": [
            {
                "question_key": "ico_11_1",
                "question_text": "Which data subject rights apply and how can they be exercised?",
                "guidance": "Document the rights available to individuals (access, rectification, erasure, restriction, portability, objection, rights in relation to automated decisions) and the mechanisms for exercising them.",
                "question_order": 1,
                "required": False,
                "fides_sources": "{privacy_experience,policy.drp_action}",
                "expected_coverage": "partial",
            },
            {
                "question_key": "ico_11_2",
                "question_text": "Link to the privacy policy applicable to this processing.",
                "guidance": "URL or reference to the public privacy policy.",
                "question_order": 2,
                "required": False,
                "fides_sources": "{privacy_notice.name}",
                "expected_coverage": "partial",
            },
            {
                "question_key": "ico_11_3",
                "question_text": "Link to any processing-specific privacy notices.",
                "guidance": "Reference to just-in-time notices, layered notices, or sector-specific transparency information provided at collection points.",
                "question_order": 3,
                "required": False,
                "fides_sources": "{privacy_notice.name,privacy_notice.data_uses}",
                "expected_coverage": "partial",
            },
        ],
    },
    {
        "requirement_key": "consent_records",
        "requirement_title": "Consent Records (Art 7)",
        "group_order": 12,
        "questions": [
            {
                "question_key": "ico_12_1",
                "question_text": "Link to the record of consent.",
                "guidance": "Where consent is the lawful basis (Article 6(1)(a)) or explicit consent is the Article 9 condition, maintain a demonstrable record of consent per Article 7(1). Reference the consent management system or log.",
                "question_order": 1,
                "required": True,
                "fides_sources": "{}",
                "expected_coverage": "none",
            },
        ],
    },
    {
        "requirement_key": "breach_notification",
        "requirement_title": "Personal Data Breaches (Art 33)",
        "group_order": 13,
        "questions": [
            {
                "question_key": "ico_13_1",
                "question_text": "How are personal data breaches notified and recorded for this processing?",
                "guidance": "Describe the breach notification workflow, including the 72-hour notification obligation to the ICO under Article 33 and notification to data subjects under Article 34 where the threshold is met.",
                "question_order": 1,
                "required": True,
                "fides_sources": "{}",
                "expected_coverage": "none",
            },
            {
                "question_key": "ico_13_2",
                "question_text": "Link to the record of personal data breaches.",
                "guidance": "Reference to the internal register of breaches maintained under Article 33(5).",
                "question_order": 2,
                "required": True,
                "fides_sources": "{}",
                "expected_coverage": "none",
            },
        ],
    },
    {
        "requirement_key": "processor_arrangements",
        "requirement_title": "Processor Arrangements",
        "group_order": 14,
        "questions": [
            {
                "question_key": "ico_14_1",
                "question_text": "Link to the processor contract (Article 28).",
                "guidance": "Where processors are used, link to the Article 28 data processing agreement.",
                "question_order": 1,
                "required": False,
                "fides_sources": "{}",
                "expected_coverage": "none",
            },
        ],
    },
    {
        "requirement_key": "review",
        "requirement_title": "Review",
        "group_order": 15,
        "questions": [
            {
                "question_key": "ico_15_1",
                "question_text": "When was this ROPA entry last reviewed and by whom?",
                "guidance": "ROPAs should be reviewed regularly and whenever the processing activity changes. Document the last review date, the reviewer, and the scheduled next review.",
                "question_order": 1,
                "required": False,
                "fides_sources": "{}",
                "expected_coverage": "none",
            },
        ],
    },
]


def upgrade() -> None:
    conn = op.get_bind()
    now = datetime.now(timezone.utc)

    # Check if template already exists
    result = conn.execute(
        sa.text(
            "SELECT id FROM assessment_template WHERE assessment_type = :assessment_type"
        ),
        {"assessment_type": ASSESSMENT_TEMPLATE["assessment_type"]},
    )
    row = result.fetchone()

    if row:
        print(
            f"Template {ASSESSMENT_TEMPLATE['assessment_type']} already exists, skipping"
        )
        template_id = row[0]
    else:
        template_id = generate_id("ast")
        conn.execute(
            sa.text("""
                INSERT INTO assessment_template (id, version, name, assessment_type, region, authority, legal_reference, description, is_active, fides_revision, is_managed, created_at, updated_at)
                VALUES (:id, :version, :name, :assessment_type, :region, :authority, :legal_reference, :description, :is_active, :fides_revision, :is_managed, :created_at, :updated_at)
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
        print(f"Created template: {ASSESSMENT_TEMPLATE['assessment_type']}")

    # Check if questions already exist
    result = conn.execute(
        sa.text(
            "SELECT COUNT(*) FROM assessment_question WHERE template_id = :template_id"
        ),
        {"template_id": template_id},
    )
    count = result.fetchone()[0]
    if count > 0:
        print(
            f"Template {ASSESSMENT_TEMPLATE['assessment_type']} already has {count} questions, skipping"
        )
        return

    # Seed questions
    question_count = 0
    for group in TEMPLATE_QUESTIONS:
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

    print(
        f"Seeded {question_count} questions for {ASSESSMENT_TEMPLATE['assessment_type']}"
    )


def downgrade() -> None:
    conn = op.get_bind()

    result = conn.execute(
        sa.text(
            "SELECT id FROM assessment_template WHERE assessment_type = :assessment_type"
        ),
        {"assessment_type": ASSESSMENT_TEMPLATE["assessment_type"]},
    )
    row = result.fetchone()

    if row:
        template_id = row[0]
        conn.execute(
            sa.text("DELETE FROM assessment_question WHERE template_id = :template_id"),
            {"template_id": template_id},
        )
        conn.execute(
            sa.text("DELETE FROM assessment_template WHERE id = :id"),
            {"id": template_id},
        )
        print(f"Deleted template: {ASSESSMENT_TEMPLATE['assessment_type']}")
