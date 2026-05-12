"""add EU AI Act FRIA 2026 assessment template

Deactivates the previous EU AI Act FRIA template and seeds the updated
v2026 template with 24 questions across 6 sections.

Revision ID: 17e350c9f4c4
Revises: b075e9f80d20
Create Date: 2026-04-17 12:00:00.000000

"""

import uuid
from datetime import datetime, timezone

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "17e350c9f4c4"
down_revision = "b075e9f80d20"
branch_labels = None
depends_on = None


def generate_id(prefix: str) -> str:
    """Generate a prefixed UUID."""
    return f"{prefix}_{uuid.uuid4()}"


ASSESSMENT_TEMPLATE = {
    "assessment_type": "eu_ai_act_fria",
    "version": "EU-AIA-FRIA-2026-08-02",
    "fides_revision": 1,
    "name": "EU AI Act Fundamental Rights Impact Assessment",
    "region": "European Union",
    "authority": "European Commission / EU AI Office",
    "legal_reference": "EU AI Act (Regulation 2024/1689), Article 27",
    "description": (
        "Fundamental rights impact assessment required for deployers of"
        " high-risk AI systems under the EU AI Act.\n\nApplicability: The"
        " FRIA obligation under Article 27 applies from 2 August 2026, when"
        " the Regulation's high-risk AI system provisions become applicable."
        " The assessment must be performed before the first use of the"
        " high-risk AI system.\n\nRelationship to the AI Office template:"
        " Article 27(5) requires the AI Office to publish a standardised"
        " questionnaire template that deployers must use when notifying the"
        " market surveillance authority of FRIA results under Article 27(3)."
        " Sections 6.5 and 6.6 of this template capture whether the AI"
        " Office template has been completed and whether notification has"
        " been made."
    ),
    "is_active": True,
    "is_managed": True,
}

TEMPLATE_QUESTIONS = [
    {
        "requirement_key": "process_and_purpose",
        "requirement_title": "Process and Purpose",
        "group_order": 1,
        "questions": [
            {
                "question_key": "fria_1_0",
                "question_text": "Under which EU AI Act classification is this AI system considered high-risk?",
                "guidance": "Identify whether the system is high-risk under Article 6(1) (safety component of regulated product) or Article 6(2) (Annex III category). If Annex III, specify which of the 8 categories applies: Biometrics, Critical Infrastructure, Education, Employment, Essential Services, Law Enforcement, Migration/Asylum, or Justice/Democratic Processes. Note that systems used as safety components in the management of critical digital infrastructure, road traffic, or the supply of water/gas/heating/electricity are exempt from the FRIA obligation.",
                "question_order": 0,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
            {
                "question_key": "fria_1_1",
                "question_text": "What is the name and description of the high-risk AI system being deployed?",
                "guidance": "Identify the AI system by its commercial name, version, and the AI provider. Include the intended purpose as stated in the provider's instructions for use.",
                "question_order": 1,
                "required": True,
                "fides_sources": ["system.name", "system.description"],
                "expected_coverage": "partial",
            },
            {
                "question_key": "fria_1_2",
                "question_text": "What are the specific business or operational processes in which this AI system will be used?",
                "guidance": "Describe the exact workflows where the AI is integrated and what decisions it informs. Reference the intended purpose defined by the AI provider. Confirm that your intended use aligns with the intended purpose defined in the provider's instructions for use. Deployment outside the intended purpose may not be covered by the provider's conformity assessment.",
                "question_order": 2,
                "required": True,
                "fides_sources": [
                    "privacy_declaration.name",
                    "privacy_declaration.data_use",
                ],
                "expected_coverage": "partial",
            },
            {
                "question_key": "fria_1_3",
                "question_text": "What categories of personal data are processed by the AI system?",
                "guidance": "List all categories of personal data used as inputs to or generated as outputs by the AI system, including any special category data under GDPR Article 9.",
                "question_order": 3,
                "required": True,
                "fides_sources": [
                    "privacy_declaration.data_categories",
                    "data_category.name",
                ],
                "expected_coverage": "full",
            },
            {
                "question_key": "fria_1_4",
                "question_text": "Has a Data Protection Impact Assessment (DPIA) been conducted for this AI system?",
                "guidance": "Article 27(4) allows a DPIA to be reused where the relevant obligations are already met, and the FRIA shall complement that DPIA. If a linked DPIA exists, identify which FRIA requirements it already addresses (typically around data categories, data subjects, technical safeguards, and privacy risks) and which require additional FRIA-specific assessment (fundamental rights beyond privacy, such as non-discrimination, dignity, freedom of expression, and access to justice).",
                "question_order": 4,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
        ],
    },
    {
        "requirement_key": "duration_and_frequency",
        "requirement_title": "Duration and Frequency",
        "group_order": 2,
        "questions": [
            {
                "question_key": "fria_2_1",
                "question_text": "What is the intended period of deployment for this AI system?",
                "guidance": "Specify whether this is a permanent deployment, a fixed-term pilot, or a time-limited use. Include start and expected end dates where applicable.",
                "question_order": 1,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
            {
                "question_key": "fria_2_2",
                "question_text": "How frequently will the AI system be used and in what operational pattern?",
                "guidance": "Describe whether the system runs continuously (24/7), on a scheduled basis (e.g., batch processing), on-demand, or during specific periods (e.g., annual reviews).",
                "question_order": 2,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
        ],
    },
    {
        "requirement_key": "affected_populations",
        "requirement_title": "Affected Populations",
        "group_order": 3,
        "questions": [
            {
                "question_key": "fria_3_1",
                "question_text": "What categories of natural persons and groups are likely to be affected by the AI system?",
                "guidance": "Identify all individuals the AI will interact with, evaluate, or make decisions about, both directly and indirectly.",
                "question_order": 1,
                "required": True,
                "fides_sources": ["privacy_declaration.data_subjects"],
                "expected_coverage": "partial",
            },
            {
                "question_key": "fria_3_2",
                "question_text": "Are any vulnerable or historically marginalized groups among the affected populations?",
                "guidance": "Assess whether the AI may affect people based on protected characteristics (race, age, gender, disability, socioeconomic status, etc.) who could be disproportionately impacted.",
                "question_order": 2,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
            {
                "question_key": "fria_3_3",
                "question_text": "What is the estimated scale of affected individuals?",
                "guidance": "Provide an estimate of how many people will be subject to the AI system's outputs, broken down by affected group where possible. Consider both individuals directly subject to AI decisions and those indirectly affected (e.g., family members, communities).",
                "question_order": 3,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
        ],
    },
    {
        "requirement_key": "risk_identification",
        "requirement_title": "Risk Identification",
        "group_order": 4,
        "questions": [
            {
                "question_key": "fria_4_1",
                "question_text": "What specific risks of harm to fundamental rights have been identified?",
                "guidance": "Evaluate how the AI could infringe upon rights in the EU Charter of Fundamental Rights, including non-discrimination (Art. 21), privacy (Art. 7-8), human dignity (Art. 1), freedom of expression (Art. 11), and access to justice (Art. 47). Base your analysis on the technical documentation provided by the AI provider.",
                "question_order": 1,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
            {
                "question_key": "fria_4_2",
                "question_text": "What is the likelihood and severity of each identified risk?",
                "guidance": "For each risk, assess how probable it is that the harm materializes and how serious the impact would be on affected individuals. Consider both individual and collective harms.",
                "question_order": 2,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
            {
                "question_key": "fria_4_3",
                "question_text": "Are there risks of bias or discriminatory outcomes in the AI system's outputs?",
                "guidance": "Analyze whether the system's training data, design, or deployment context could lead to biased or discriminatory results, particularly for the vulnerable groups identified. Reference the AI provider's bias testing documentation.",
                "question_order": 3,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
        ],
    },
    {
        "requirement_key": "human_oversight",
        "requirement_title": "Human Oversight",
        "group_order": 5,
        "questions": [
            {
                "question_key": "fria_5_1",
                "question_text": "What human oversight measures are in place for this AI system?",
                "guidance": "Describe who monitors the system, their qualifications, and the frequency of oversight. Reference the human oversight instructions provided by the AI provider per Article 14.",
                "question_order": 1,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
            {
                "question_key": "fria_5_2",
                "question_text": "What authority do human overseers have to intervene in or override the AI's decisions?",
                "guidance": "Detail the mechanisms for overriding, reversing, or halting the AI's outputs. Explain at what points human review occurs and whether the AI can act autonomously.",
                "question_order": 2,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
            {
                "question_key": "fria_5_3",
                "question_text": "What training is provided to prevent automation bias among human overseers?",
                "guidance": "Describe training programs to ensure overseers critically evaluate AI outputs rather than defaulting to automated recommendations.",
                "question_order": 3,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
        ],
    },
    {
        "requirement_key": "mitigation_and_governance",
        "requirement_title": "Mitigation and Governance",
        "group_order": 6,
        "questions": [
            {
                "question_key": "fria_6_1",
                "question_text": "What measures will be taken if identified risks materialize?",
                "guidance": "Detail incident response protocols, including how the AI system can be halted, how affected individuals will be notified, and what remediation steps will follow.",
                "question_order": 1,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
            {
                "question_key": "fria_6_2",
                "question_text": "What internal governance arrangements are in place for this AI system?",
                "guidance": "Describe the organizational structure responsible for AI governance, including roles, escalation paths, and review cadences.",
                "question_order": 2,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
            {
                "question_key": "fria_6_3",
                "question_text": "What complaint mechanisms are available to individuals affected by the AI system?",
                "guidance": "Describe how affected individuals can challenge the AI's decisions, submit complaints, and seek redress. Include both internal complaint processes and external reporting channels.",
                "question_order": 3,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
            {
                "question_key": "fria_6_4",
                "question_text": "What process is in place to review and update this FRIA when circumstances change?",
                "guidance": "Article 27(2) requires updating the FRIA when any element changes. Describe the triggers for review (e.g., system updates, changes in affected populations, new risks identified) and the review frequency.",
                "question_order": 4,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
            {
                "question_key": "fria_6_5",
                "question_text": "Has the Article 27(5) AI Office template been completed for this FRIA?",
                "guidance": "Article 27(5) requires the AI Office to publish a standardised questionnaire that deployers must use when notifying the market surveillance authority. Record the status as \"completed / not yet completed / not applicable (exempt)\" and attach the filled template. If the AI Office template is not yet published at the time of assessment, document the interim approach taken and the plan to re-submit using the official template once available.",
                "question_order": 5,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
            {
                "question_key": "fria_6_6",
                "question_text": "Has the completed FRIA been notified to the relevant market surveillance authority?",
                "guidance": "Article 27(3) requires deployers to notify the market surveillance authority of the FRIA results, submitting the Article 27(5) template as part of the notification. Document the notification date and authority contacted.",
                "question_order": 6,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
            {
                "question_key": "fria_6_7",
                "question_text": "Does an Article 46(1) exemption from the notification obligation apply?",
                "guidance": "Article 27(3) provides that deployers may be exempt from the notification obligation in the circumstances referred to in Article 46(1) (e.g., exceptional reasons of public security). If claiming an exemption, document the legal basis and the specific justification.",
                "question_order": 7,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
            {
                "question_key": "fria_6_8",
                "question_text": "Pre-deployment gating confirmation.",
                "guidance": "Confirm that the FRIA has been completed and (where applicable) notified to the market surveillance authority before the AI system is put into use. Article 27(1) requires the FRIA to be performed prior to deployment; a retrospective FRIA does not satisfy the obligation. Any workflow linking this FRIA to a system inventory should block transition to a \"deployed\" state until this confirmation is recorded.",
                "question_order": 8,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
        ],
    },
]

# Old template version for downgrade re-activation
OLD_TEMPLATE_VERSION = "EU-AIA-FRIA-2024-08-01"


def _format_fides_sources(sources: list[str]) -> str:
    """Format a list of fides_sources as a PostgreSQL array literal."""
    if not sources:
        return "{}"
    return "{" + ",".join(sources) + "}"


def upgrade() -> None:
    conn = op.get_bind()
    now = datetime.now(timezone.utc)

    # Step 1: Deactivate the old FRIA template
    conn.execute(
        sa.text(
            "UPDATE assessment_template SET is_active = false"
            " WHERE assessment_type = 'eu_ai_act_fria' AND is_active = true"
        ),
    )
    print("Deactivated old eu_ai_act_fria template(s)")

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
            " WHERE assessment_type = 'eu_ai_act_fria'"
            " AND version = :old_version"
        ),
        {"old_version": OLD_TEMPLATE_VERSION},
    )
    print(f"Re-activated old eu_ai_act_fria template v{OLD_TEMPLATE_VERSION}")
