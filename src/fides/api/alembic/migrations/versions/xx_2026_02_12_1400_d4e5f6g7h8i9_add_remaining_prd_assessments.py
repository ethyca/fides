"""add remaining PRD assessment templates and questions

This migration adds the following assessment templates per the PRD:
- UK GDPR DPIA (based on ICO guidance and UK GDPR/DPA 2018)
- Colorado CPA Data Protection Assessment (based on C.R.S. § 6-1-1309 and 4 CCR 904-3)
- Virginia VCDPA Data Protection Assessment (based on Va. Code Ann. § 59.1-580)
- US Multi-State DPA (generic template for state privacy laws)
- Generic Best Practice PIA (based on CNIL PIA methodology)

Revision ID: d4e5f6g7h8i9
Revises: c3d4e5f6g7h8
Create Date: 2026-02-12 14:00:00.000000

"""

import uuid
from datetime import datetime, timezone

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "d4e5f6g7h8i9"
down_revision = "c3d4e5f6g7h8"
branch_labels = None
depends_on = None


def generate_id(prefix: str) -> str:
    """Generate a prefixed UUID."""
    return f"{prefix}_{uuid.uuid4()}"


# Assessment Templates to Add
ASSESSMENT_TEMPLATES = [
    {
        "key": "uk_gdpr_dpia",
        "version": "UK-GDPR-DPIA-ICO-2024",
        "name": "UK GDPR Data Protection Impact Assessment (DPIA)",
        "assessment_type": "dpia",
        "region": "United Kingdom",
        "authority": "Information Commissioner's Office (ICO)",
        "legal_reference": "UK GDPR Article 35, Data Protection Act 2018 Section 64, ICO DPIA Guidance, Age Appropriate Design Code",
        "description": "UK regulator-aligned DPIA process and documentation. Required when processing is likely to result in a high risk to individuals' rights and freedoms.",
        "is_active": True,
    },
    {
        "key": "us_co_cpa_dpa",
        "version": "US-CO-CPA-DPA-2024",
        "name": "Colorado Privacy Act Data Protection Assessment (DPA)",
        "assessment_type": "dpa",
        "region": "United States (Colorado)",
        "authority": "Colorado Attorney General",
        "legal_reference": "Colo. Rev. Stat. § 6-1-1309, Colorado Privacy Act Rules 4 CCR 904-3 Part 8",
        "description": "Assessment weighing benefits of processing against risks for heightened-risk processing including targeted advertising, profiling, sale of personal data, and sensitive data processing.",
        "is_active": True,
    },
    {
        "key": "us_va_vcdpa_dpa",
        "version": "US-VA-VCDPA-DPA-2024",
        "name": "Virginia Consumer Data Protection Act Data Protection Assessment (DPA)",
        "assessment_type": "dpa",
        "region": "United States (Virginia)",
        "authority": "Virginia Attorney General",
        "legal_reference": "Va. Code Ann. § 59.1-580",
        "description": "Assessment for processing presenting heightened risk of harm to consumers, including targeted advertising, sale of personal data, profiling, and sensitive data processing.",
        "is_active": True,
    },
    {
        "key": "us_multi_state_dpa",
        "version": "US-MULTI-STATE-DPA-2024",
        "name": "US State Privacy Law Data Protection Assessment (Generic)",
        "assessment_type": "dpa",
        "region": "United States (Multi-State)",
        "authority": "Various State Attorneys General",
        "legal_reference": "Generic DPA template aligned with CO CPA, VA VCDPA, CT CTDPA, and other state privacy laws",
        "description": "A unified template that can be parameterized per state law and processing trigger. Covers common DPA requirements across multiple US state privacy laws.",
        "is_active": True,
    },
    {
        "key": "best_practice_pia",
        "version": "BP-PIA-2024",
        "name": "Generic Privacy Impact Assessment (Best Practice)",
        "assessment_type": "pia",
        "region": "Global",
        "authority": "Best Practice / Industry Standards",
        "legal_reference": "CNIL PIA methodology, ISO 29134, NIST Privacy Framework",
        "description": "A regulator-neutral PIA template usable when no explicit legal template exists. Based on industry best practices and common DPIA patterns.",
        "is_active": True,
    },
]


# UK GDPR DPIA Questions (based on ICO guidance)
UK_GDPR_DPIA_QUESTIONS = [
    # Group 1: Processing Description
    {
        "requirement_key": "processing_description",
        "requirement_title": "Description of Processing",
        "group_order": 1,
        "questions": [
            {
                "question_key": "uk_dpia_1_1",
                "question_text": "Describe the nature of the processing: how will you collect, use, store and delete data?",
                "guidance": "Include what data you will collect, who from, how it will be used, who has access, and how it will be disposed of.",
                "question_order": 1,
                "required": True,
                "fides_sources": ["system.name", "system.description", "privacy_declaration.name"],
                "expected_coverage": "partial",
            },
            {
                "question_key": "uk_dpia_1_2",
                "question_text": "What is the scope of the processing?",
                "guidance": "Describe the categories of personal data, volume of data, frequency of processing, retention period, number of data subjects affected, and geographical coverage.",
                "question_order": 2,
                "required": True,
                "fides_sources": ["privacy_declaration.data_categories", "privacy_declaration.data_subjects"],
                "expected_coverage": "partial",
            },
            {
                "question_key": "uk_dpia_1_3",
                "question_text": "What is the context of the processing?",
                "guidance": "Consider your relationship with the individuals, how much control they have, whether they would expect this processing, and any relevant industry standards.",
                "question_order": 3,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
            {
                "question_key": "uk_dpia_1_4",
                "question_text": "What are the purposes of the processing?",
                "guidance": "Describe why you want to process the data and the intended outcome for individuals.",
                "question_order": 4,
                "required": True,
                "fides_sources": ["privacy_declaration.data_use", "data_use.name", "data_use.description"],
                "expected_coverage": "full",
            },
        ],
    },
    # Group 2: Consultation
    {
        "requirement_key": "consultation",
        "requirement_title": "Consultation",
        "group_order": 2,
        "questions": [
            {
                "question_key": "uk_dpia_2_1",
                "question_text": "Have you consulted with your Data Protection Officer (DPO)?",
                "guidance": "Document the DPO's advice and any recommendations provided.",
                "question_order": 1,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
            {
                "question_key": "uk_dpia_2_2",
                "question_text": "Have you sought the views of data subjects or their representatives?",
                "guidance": "If not, explain why this was not appropriate or possible. Consider focus groups, surveys, or consultation with advocacy groups.",
                "question_order": 2,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
            {
                "question_key": "uk_dpia_2_3",
                "question_text": "Have you consulted with any other stakeholders (e.g., security, IT, legal)?",
                "guidance": "Document any internal or external consultation and key findings.",
                "question_order": 3,
                "required": False,
                "fides_sources": [],
                "expected_coverage": "none",
            },
        ],
    },
    # Group 3: Necessity and Proportionality
    {
        "requirement_key": "necessity_proportionality",
        "requirement_title": "Necessity and Proportionality Assessment",
        "group_order": 3,
        "questions": [
            {
                "question_key": "uk_dpia_3_1",
                "question_text": "What is your lawful basis for processing?",
                "guidance": "Identify the lawful basis under UK GDPR Article 6. If processing special category data, also identify the condition under Article 9.",
                "question_order": 1,
                "required": True,
                "fides_sources": ["privacy_declaration.legal_basis_for_processing"],
                "expected_coverage": "full",
            },
            {
                "question_key": "uk_dpia_3_2",
                "question_text": "How will you ensure data quality and data minimisation?",
                "guidance": "Explain how you will ensure data is accurate, adequate, relevant, and limited to what is necessary.",
                "question_order": 2,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
            {
                "question_key": "uk_dpia_3_3",
                "question_text": "How will you support data subject rights?",
                "guidance": "Describe how individuals can exercise rights including access, rectification, erasure, restriction, portability, and objection.",
                "question_order": 3,
                "required": True,
                "fides_sources": ["privacy_experience", "policy.drp_action"],
                "expected_coverage": "partial",
            },
            {
                "question_key": "uk_dpia_3_4",
                "question_text": "What safeguards are in place for any international data transfers?",
                "guidance": "Identify transfer mechanisms such as adequacy decisions, SCCs, BCRs, or approved derogations.",
                "question_order": 4,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
        ],
    },
    # Group 4: Risk Assessment
    {
        "requirement_key": "risk_assessment",
        "requirement_title": "Risk Assessment",
        "group_order": 4,
        "questions": [
            {
                "question_key": "uk_dpia_4_1",
                "question_text": "What are the potential risks to individuals from this processing?",
                "guidance": "Consider risks including discrimination, identity theft, financial loss, reputational damage, loss of confidentiality, physical harm, or psychological harm.",
                "question_order": 1,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
            {
                "question_key": "uk_dpia_4_2",
                "question_text": "What is the likelihood and severity of each identified risk?",
                "guidance": "Assess each risk considering both probability (remote, possible, probable) and severity (minimal, significant, severe).",
                "question_order": 2,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
            {
                "question_key": "uk_dpia_4_3",
                "question_text": "Does the processing involve special category data or data relating to criminal convictions?",
                "guidance": "Special categories include health, genetic, biometric, racial/ethnic origin, political opinions, religious beliefs, trade union membership, sex life/orientation.",
                "question_order": 3,
                "required": True,
                "fides_sources": ["privacy_declaration.data_categories"],
                "expected_coverage": "full",
            },
        ],
    },
    # Group 5: Children and Vulnerable Groups
    {
        "requirement_key": "children_vulnerable",
        "requirement_title": "Children and Vulnerable Groups (Age Appropriate Design)",
        "group_order": 5,
        "questions": [
            {
                "question_key": "uk_dpia_5_1",
                "question_text": "Is the service/processing likely to be accessed by children (under 18)?",
                "guidance": "Consider whether children are part of your intended audience or whether they might access the service regardless.",
                "question_order": 1,
                "required": True,
                "fides_sources": ["privacy_declaration.data_subjects"],
                "expected_coverage": "partial",
            },
            {
                "question_key": "uk_dpia_5_2",
                "question_text": "If children may be affected, what additional safeguards are in place?",
                "guidance": "Consider the ICO Age Appropriate Design Code standards including best interests of the child, default settings, data minimisation, and parental controls.",
                "question_order": 2,
                "required": False,
                "fides_sources": [],
                "expected_coverage": "none",
            },
            {
                "question_key": "uk_dpia_5_3",
                "question_text": "Does the processing involve vulnerable individuals (employees, elderly, patients)?",
                "guidance": "Vulnerable individuals may have restricted ability to consent or understand implications of processing.",
                "question_order": 3,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
        ],
    },
    # Group 6: Risk Mitigation
    {
        "requirement_key": "risk_mitigation",
        "requirement_title": "Risk Mitigation Measures",
        "group_order": 6,
        "questions": [
            {
                "question_key": "uk_dpia_6_1",
                "question_text": "What measures will you take to address and mitigate the identified risks?",
                "guidance": "List technical and organisational measures to reduce each identified risk.",
                "question_order": 1,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
            {
                "question_key": "uk_dpia_6_2",
                "question_text": "What is the residual risk level after mitigation measures?",
                "guidance": "Assess whether the remaining risk is acceptable or whether further measures are needed.",
                "question_order": 2,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
            {
                "question_key": "uk_dpia_6_3",
                "question_text": "Is prior consultation with the ICO required?",
                "guidance": "Required if high residual risk remains that cannot be mitigated. The ICO must be consulted before processing begins.",
                "question_order": 3,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
        ],
    },
    # Group 7: Transparency
    {
        "requirement_key": "transparency",
        "requirement_title": "Transparency and Privacy Information",
        "group_order": 7,
        "questions": [
            {
                "question_key": "uk_dpia_7_1",
                "question_text": "How will you inform data subjects about the processing?",
                "guidance": "Describe the privacy notice or information provided, including timing and delivery method.",
                "question_order": 1,
                "required": True,
                "fides_sources": ["privacy_notice.name", "privacy_notice.data_uses"],
                "expected_coverage": "partial",
            },
        ],
    },
    # Group 8: Sign-off and Review
    {
        "requirement_key": "sign_off_review",
        "requirement_title": "Sign-off and Review",
        "group_order": 8,
        "questions": [
            {
                "question_key": "uk_dpia_8_1",
                "question_text": "Who has approved this DPIA and when?",
                "guidance": "Document the names, roles, and sign-off dates of approvers.",
                "question_order": 1,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
            {
                "question_key": "uk_dpia_8_2",
                "question_text": "When will this DPIA be reviewed and by whom?",
                "guidance": "DPIAs should be regularly reviewed and updated when processing changes.",
                "question_order": 2,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
        ],
    },
]


# Colorado CPA DPA Questions (based on 4 CCR 904-3-8.04)
COLORADO_CPA_DPA_QUESTIONS = [
    # Group 1: Processing Description
    {
        "requirement_key": "processing_description",
        "requirement_title": "Processing Description and Context",
        "group_order": 1,
        "questions": [
            {
                "question_key": "co_dpa_1_1",
                "question_text": "Provide a short summary of the processing activity.",
                "guidance": "Describe the processing activity in plain language, including its business purpose.",
                "question_order": 1,
                "required": True,
                "fides_sources": ["system.name", "system.description"],
                "expected_coverage": "partial",
            },
            {
                "question_key": "co_dpa_1_2",
                "question_text": "What categories of personal data are processed?",
                "guidance": "List all data categories, specifically identifying any sensitive data or data involving minors.",
                "question_order": 2,
                "required": True,
                "fides_sources": ["privacy_declaration.data_categories"],
                "expected_coverage": "full",
            },
            {
                "question_key": "co_dpa_1_3",
                "question_text": "What is the context of the processing, including controller-consumer relationships?",
                "guidance": "Describe the relationship with consumers and their reasonable expectations.",
                "question_order": 3,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
            {
                "question_key": "co_dpa_1_4",
                "question_text": "Describe the nature and operational elements of the processing.",
                "guidance": "Include data type, amount, sensitivity, and risk impacts on consumers.",
                "question_order": 4,
                "required": True,
                "fides_sources": ["privacy_declaration.data_use"],
                "expected_coverage": "partial",
            },
        ],
    },
    # Group 2: Purposes and Benefits
    {
        "requirement_key": "purposes_benefits",
        "requirement_title": "Purposes and Benefits",
        "group_order": 2,
        "questions": [
            {
                "question_key": "co_dpa_2_1",
                "question_text": "What are the core purposes of this processing?",
                "guidance": "Describe the primary purposes including whether the processing involves targeted advertising, profiling, sale of data, or sensitive data.",
                "question_order": 1,
                "required": True,
                "fides_sources": ["privacy_declaration.data_use", "data_use.name"],
                "expected_coverage": "full",
            },
            {
                "question_key": "co_dpa_2_2",
                "question_text": "What are the benefits to the controller?",
                "guidance": "Describe business value and operational benefits of the processing.",
                "question_order": 2,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
            {
                "question_key": "co_dpa_2_3",
                "question_text": "What are the benefits to consumers?",
                "guidance": "Describe how consumers directly benefit from this processing.",
                "question_order": 3,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
            {
                "question_key": "co_dpa_2_4",
                "question_text": "What are the benefits to other stakeholders and the public?",
                "guidance": "Consider broader societal benefits beyond the direct parties.",
                "question_order": 4,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
        ],
    },
    # Group 3: Risk Identification
    {
        "requirement_key": "risk_identification",
        "requirement_title": "Risk Identification",
        "group_order": 3,
        "questions": [
            {
                "question_key": "co_dpa_3_1",
                "question_text": "What are the sources and nature of risks to consumer rights?",
                "guidance": "Per 4 CCR 904-3-8.04(6), identify risks including: constitutional harms, intellectual privacy injuries, security breaches, discrimination, unfair treatment, financial injury, physical harm, privacy violations, psychological damage, and other detrimental consequences.",
                "question_order": 1,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
            {
                "question_key": "co_dpa_3_2",
                "question_text": "Could this processing result in unfair or deceptive treatment of consumers?",
                "guidance": "Assess risk of discriminatory outcomes or deceptive practices.",
                "question_order": 2,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
            {
                "question_key": "co_dpa_3_3",
                "question_text": "Could this processing result in unlawful disparate impact?",
                "guidance": "Consider whether the processing could disproportionately affect protected classes.",
                "question_order": 3,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
            {
                "question_key": "co_dpa_3_4",
                "question_text": "Could this processing result in financial, physical, or reputational injury?",
                "guidance": "Assess potential for tangible harm to consumers.",
                "question_order": 4,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
        ],
    },
    # Group 4: Safeguards and Mitigation
    {
        "requirement_key": "safeguards_mitigation",
        "requirement_title": "Safeguards and Mitigation",
        "group_order": 4,
        "questions": [
            {
                "question_key": "co_dpa_4_1",
                "question_text": "What data security practices are implemented per C.R.S. § 6-1-1308?",
                "guidance": "Document technical and organizational security measures.",
                "question_order": 1,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
            {
                "question_key": "co_dpa_4_2",
                "question_text": "What consent compliance measures are in place?",
                "guidance": "Describe how consumer consent is obtained and managed.",
                "question_order": 2,
                "required": True,
                "fides_sources": ["privacy_experience"],
                "expected_coverage": "partial",
            },
            {
                "question_key": "co_dpa_4_3",
                "question_text": "What contractual agreements exist with processors and third parties?",
                "guidance": "Document data processing agreements and third-party contracts.",
                "question_order": 3,
                "required": True,
                "fides_sources": ["privacy_declaration.third_parties"],
                "expected_coverage": "partial",
            },
            {
                "question_key": "co_dpa_4_4",
                "question_text": "Is de-identified data used where possible?",
                "guidance": "Describe use of de-identification techniques to reduce risk.",
                "question_order": 4,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
            {
                "question_key": "co_dpa_4_5",
                "question_text": "How can consumers access and exercise their rights?",
                "guidance": "Document consumer rights access mechanisms.",
                "question_order": 5,
                "required": True,
                "fides_sources": ["privacy_experience", "policy.drp_action"],
                "expected_coverage": "partial",
            },
        ],
    },
    # Group 5: Benefits vs Risks Conclusion
    {
        "requirement_key": "benefits_vs_risks",
        "requirement_title": "Benefits vs. Risks Analysis",
        "group_order": 5,
        "questions": [
            {
                "question_key": "co_dpa_5_1",
                "question_text": "How do the benefits of processing outweigh the identified risks, as mitigated by safeguards?",
                "guidance": "Per C.R.S. § 6-1-1309(3), the assessment must demonstrate how benefits outweigh identified risks after applying safeguards.",
                "question_order": 1,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
        ],
    },
    # Group 6: Profiling-Specific (if applicable)
    {
        "requirement_key": "profiling_specific",
        "requirement_title": "Profiling-Specific Requirements",
        "group_order": 6,
        "questions": [
            {
                "question_key": "co_dpa_6_1",
                "question_text": "If profiling is involved, what types of personal data are used?",
                "guidance": "Per 4 CCR 904-3-9.06, identify all data categories used in profiling.",
                "question_order": 1,
                "required": False,
                "fides_sources": ["privacy_declaration.data_categories"],
                "expected_coverage": "full",
            },
            {
                "question_key": "co_dpa_6_2",
                "question_text": "Provide a plain language explanation of the profiling logic.",
                "guidance": "Explain in understandable terms why the profiling relates to your goods/services.",
                "question_order": 2,
                "required": False,
                "fides_sources": [],
                "expected_coverage": "none",
            },
            {
                "question_key": "co_dpa_6_3",
                "question_text": "What training data and logic are used in automated processing?",
                "guidance": "Document the basis for automated analysis and decision-making.",
                "question_order": 3,
                "required": False,
                "fides_sources": [],
                "expected_coverage": "none",
            },
        ],
    },
    # Group 7: Documentation and Approval
    {
        "requirement_key": "documentation_approval",
        "requirement_title": "Documentation and Approval",
        "group_order": 7,
        "questions": [
            {
                "question_key": "co_dpa_7_1",
                "question_text": "Have any internal or external audits been conducted?",
                "guidance": "Document auditor name, individuals involved, and audit process.",
                "question_order": 1,
                "required": False,
                "fides_sources": [],
                "expected_coverage": "none",
            },
            {
                "question_key": "co_dpa_7_2",
                "question_text": "Who reviewed and approved this assessment?",
                "guidance": "Document names, positions, and signatures of responsible individuals.",
                "question_order": 2,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
            {
                "question_key": "co_dpa_7_3",
                "question_text": "When will this assessment be reviewed?",
                "guidance": "For profiling, review must occur at least annually. Assessments must be retained for at least 3 years after processing ends.",
                "question_order": 3,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
        ],
    },
]


# Virginia VCDPA DPA Questions (based on Va. Code Ann. § 59.1-580)
VIRGINIA_VCDPA_DPA_QUESTIONS = [
    # Group 1: Processing Description
    {
        "requirement_key": "processing_description",
        "requirement_title": "Processing Description",
        "group_order": 1,
        "questions": [
            {
                "question_key": "va_dpa_1_1",
                "question_text": "Describe the processing activity and its purposes.",
                "guidance": "Provide a clear description of the processing operations.",
                "question_order": 1,
                "required": True,
                "fides_sources": ["system.name", "system.description", "privacy_declaration.data_use"],
                "expected_coverage": "partial",
            },
            {
                "question_key": "va_dpa_1_2",
                "question_text": "What triggers the requirement for this assessment?",
                "guidance": "Identify whether the processing involves: targeted advertising, sale of personal data, profiling with risk of harm, sensitive data, or other heightened risk.",
                "question_order": 2,
                "required": True,
                "fides_sources": ["privacy_declaration.data_use"],
                "expected_coverage": "partial",
            },
            {
                "question_key": "va_dpa_1_3",
                "question_text": "What categories of personal data are involved?",
                "guidance": "List all data categories including any sensitive data.",
                "question_order": 3,
                "required": True,
                "fides_sources": ["privacy_declaration.data_categories"],
                "expected_coverage": "full",
            },
            {
                "question_key": "va_dpa_1_4",
                "question_text": "What categories of consumers are affected?",
                "guidance": "Identify the groups of individuals whose data is processed.",
                "question_order": 4,
                "required": True,
                "fides_sources": ["privacy_declaration.data_subjects"],
                "expected_coverage": "full",
            },
        ],
    },
    # Group 2: Benefits Analysis
    {
        "requirement_key": "benefits_analysis",
        "requirement_title": "Benefits Analysis",
        "group_order": 2,
        "questions": [
            {
                "question_key": "va_dpa_2_1",
                "question_text": "What are the direct and indirect benefits to the controller?",
                "guidance": "Per Va. Code § 59.1-580(C), identify benefits that flow to the controller.",
                "question_order": 1,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
            {
                "question_key": "va_dpa_2_2",
                "question_text": "What are the direct and indirect benefits to consumers?",
                "guidance": "Describe how the processing benefits the individuals whose data is processed.",
                "question_order": 2,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
            {
                "question_key": "va_dpa_2_3",
                "question_text": "What are the benefits to other stakeholders and the public?",
                "guidance": "Consider broader benefits beyond the direct parties.",
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
                "question_key": "va_dpa_3_1",
                "question_text": "What are the potential risks to consumer rights from this processing?",
                "guidance": "Per Va. Code § 59.1-580(A)(3), consider risks of: unfair/deceptive treatment, unlawful disparate impact, financial/physical/reputational injury, and intrusion upon privacy.",
                "question_order": 1,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
            {
                "question_key": "va_dpa_3_2",
                "question_text": "What are consumer reasonable expectations regarding this processing?",
                "guidance": "Consider whether consumers would expect this type of processing.",
                "question_order": 2,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
            {
                "question_key": "va_dpa_3_3",
                "question_text": "What is the context of the processing and controller-consumer relationship?",
                "guidance": "Describe the nature of the relationship and any relevant context.",
                "question_order": 3,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
        ],
    },
    # Group 4: Safeguards and Mitigation
    {
        "requirement_key": "safeguards_mitigation",
        "requirement_title": "Safeguards and Mitigation",
        "group_order": 4,
        "questions": [
            {
                "question_key": "va_dpa_4_1",
                "question_text": "What safeguards are employed to reduce the identified risks?",
                "guidance": "Per Va. Code § 59.1-580(C), document safeguards that mitigate risks.",
                "question_order": 1,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
            {
                "question_key": "va_dpa_4_2",
                "question_text": "Is de-identified data used where possible?",
                "guidance": "Document the use of de-identification as a risk reduction measure.",
                "question_order": 2,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
            {
                "question_key": "va_dpa_4_3",
                "question_text": "Who are the data recipients and what is the purpose of each disclosure?",
                "guidance": "Document all recipients including service providers, contractors, and third parties.",
                "question_order": 3,
                "required": True,
                "fides_sources": ["privacy_declaration.third_parties", "connection.name"],
                "expected_coverage": "partial",
            },
        ],
    },
    # Group 5: Children's Online Services (Va. Code § 59.1-580(B))
    {
        "requirement_key": "children_services",
        "requirement_title": "Children's Online Services",
        "group_order": 5,
        "questions": [
            {
                "question_key": "va_dpa_5_1",
                "question_text": "If this is an online service directed to children, what is the purpose of the service?",
                "guidance": "Per Va. Code § 59.1-580(B), assessments for children's services must address this.",
                "question_order": 1,
                "required": False,
                "fides_sources": [],
                "expected_coverage": "none",
            },
            {
                "question_key": "va_dpa_5_2",
                "question_text": "What categories of personal data concerning children are processed?",
                "guidance": "Identify all data categories related to children's data.",
                "question_order": 2,
                "required": False,
                "fides_sources": ["privacy_declaration.data_categories"],
                "expected_coverage": "partial",
            },
            {
                "question_key": "va_dpa_5_3",
                "question_text": "What are the purposes for processing children's personal data?",
                "guidance": "Describe the specific purposes for which children's data is used.",
                "question_order": 3,
                "required": False,
                "fides_sources": ["privacy_declaration.data_use"],
                "expected_coverage": "partial",
            },
        ],
    },
    # Group 6: Benefits vs Risks Conclusion
    {
        "requirement_key": "benefits_vs_risks",
        "requirement_title": "Benefits vs. Risks Conclusion",
        "group_order": 6,
        "questions": [
            {
                "question_key": "va_dpa_6_1",
                "question_text": "Do the benefits of processing outweigh the potential risks to consumer rights, as mitigated by safeguards?",
                "guidance": "Per Va. Code § 59.1-580(C), the assessment must weigh benefits against risks after considering safeguards.",
                "question_order": 1,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
        ],
    },
    # Group 7: Retention and Data Sharing
    {
        "requirement_key": "retention_sharing",
        "requirement_title": "Retention and Data Sharing",
        "group_order": 7,
        "questions": [
            {
                "question_key": "va_dpa_7_1",
                "question_text": "What is the retention period for personal data?",
                "guidance": "Document retention periods and justification.",
                "question_order": 1,
                "required": True,
                "fides_sources": ["privacy_declaration.retention_period"],
                "expected_coverage": "partial",
            },
            {
                "question_key": "va_dpa_7_2",
                "question_text": "Is personal data sold or shared for targeted advertising?",
                "guidance": "Document whether data is sold or shared and with whom.",
                "question_order": 2,
                "required": True,
                "fides_sources": ["privacy_declaration.data_use"],
                "expected_coverage": "partial",
            },
        ],
    },
]


# US Multi-State DPA Questions (Generic template)
US_MULTI_STATE_DPA_QUESTIONS = [
    # Group 1: Processing Description
    {
        "requirement_key": "processing_description",
        "requirement_title": "Processing Description",
        "group_order": 1,
        "questions": [
            {
                "question_key": "ms_dpa_1_1",
                "question_text": "Describe the processing activity and its purposes.",
                "guidance": "Provide a clear description of the processing operations.",
                "question_order": 1,
                "required": True,
                "fides_sources": ["system.name", "system.description", "privacy_declaration.data_use"],
                "expected_coverage": "partial",
            },
            {
                "question_key": "ms_dpa_1_2",
                "question_text": "What processing triggers require this assessment?",
                "guidance": "Select all applicable triggers: targeted advertising, profiling, sale of data, sensitive data processing.",
                "question_order": 2,
                "required": True,
                "fides_sources": ["privacy_declaration.data_use"],
                "expected_coverage": "partial",
            },
            {
                "question_key": "ms_dpa_1_3",
                "question_text": "What categories of personal data are processed?",
                "guidance": "List all data categories including any sensitive data.",
                "question_order": 3,
                "required": True,
                "fides_sources": ["privacy_declaration.data_categories"],
                "expected_coverage": "full",
            },
            {
                "question_key": "ms_dpa_1_4",
                "question_text": "What categories of consumers are affected?",
                "guidance": "Identify the groups of individuals whose data is processed.",
                "question_order": 4,
                "required": True,
                "fides_sources": ["privacy_declaration.data_subjects"],
                "expected_coverage": "full",
            },
        ],
    },
    # Group 2: Benefits Analysis
    {
        "requirement_key": "benefits_analysis",
        "requirement_title": "Benefits Analysis",
        "group_order": 2,
        "questions": [
            {
                "question_key": "ms_dpa_2_1",
                "question_text": "What are the benefits of this processing to the business?",
                "guidance": "Describe business value and operational benefits.",
                "question_order": 1,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
            {
                "question_key": "ms_dpa_2_2",
                "question_text": "What are the benefits of this processing to consumers?",
                "guidance": "Describe how consumers benefit directly from this processing.",
                "question_order": 2,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
            {
                "question_key": "ms_dpa_2_3",
                "question_text": "What are the benefits to other stakeholders and the public?",
                "guidance": "Consider broader societal benefits.",
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
                "question_key": "ms_dpa_3_1",
                "question_text": "What are the potential risks to consumer rights?",
                "guidance": "Common risks include: unfair/deceptive treatment, discrimination, financial/physical/reputational injury, privacy intrusion.",
                "question_order": 1,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
            {
                "question_key": "ms_dpa_3_2",
                "question_text": "What is the likelihood and severity of each identified risk?",
                "guidance": "Assess probability and potential impact.",
                "question_order": 2,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
            {
                "question_key": "ms_dpa_3_3",
                "question_text": "What are consumer reasonable expectations?",
                "guidance": "Consider whether consumers would expect this processing.",
                "question_order": 3,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
        ],
    },
    # Group 4: Safeguards and Mitigation
    {
        "requirement_key": "safeguards_mitigation",
        "requirement_title": "Safeguards and Mitigation",
        "group_order": 4,
        "questions": [
            {
                "question_key": "ms_dpa_4_1",
                "question_text": "What safeguards are in place to mitigate the identified risks?",
                "guidance": "Document technical and organizational measures.",
                "question_order": 1,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
            {
                "question_key": "ms_dpa_4_2",
                "question_text": "Is de-identified data used where possible?",
                "guidance": "Document use of de-identification techniques.",
                "question_order": 2,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
        ],
    },
    # Group 5: Benefits vs Risks
    {
        "requirement_key": "benefits_vs_risks",
        "requirement_title": "Benefits vs. Risks Analysis",
        "group_order": 5,
        "questions": [
            {
                "question_key": "ms_dpa_5_1",
                "question_text": "Do the benefits of processing outweigh the potential risks, as mitigated by safeguards?",
                "guidance": "State privacy laws require benefits to outweigh risks after considering safeguards.",
                "question_order": 1,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
        ],
    },
    # Group 6: Data Sharing and Retention
    {
        "requirement_key": "data_sharing_retention",
        "requirement_title": "Data Sharing and Retention",
        "group_order": 6,
        "questions": [
            {
                "question_key": "ms_dpa_6_1",
                "question_text": "Who are the data recipients?",
                "guidance": "Document all recipients including service providers and third parties.",
                "question_order": 1,
                "required": True,
                "fides_sources": ["privacy_declaration.third_parties"],
                "expected_coverage": "partial",
            },
            {
                "question_key": "ms_dpa_6_2",
                "question_text": "Is personal data sold or shared for advertising?",
                "guidance": "Document sale/sharing activities and consumer opt-out mechanisms.",
                "question_order": 2,
                "required": True,
                "fides_sources": ["privacy_declaration.data_use"],
                "expected_coverage": "partial",
            },
            {
                "question_key": "ms_dpa_6_3",
                "question_text": "What is the data retention period?",
                "guidance": "Document retention periods and justification.",
                "question_order": 3,
                "required": True,
                "fides_sources": ["privacy_declaration.retention_period"],
                "expected_coverage": "partial",
            },
        ],
    },
    # Group 7: Universal Opt-Out
    {
        "requirement_key": "universal_opt_out",
        "requirement_title": "Universal Opt-Out Mechanisms",
        "group_order": 7,
        "questions": [
            {
                "question_key": "ms_dpa_7_1",
                "question_text": "How are universal opt-out signals (e.g., GPC) honored where required?",
                "guidance": "Several state laws require honoring universal opt-out mechanisms like Global Privacy Control.",
                "question_order": 1,
                "required": True,
                "fides_sources": ["fides.config"],
                "expected_coverage": "partial",
            },
        ],
    },
    # Group 8: Review and Documentation
    {
        "requirement_key": "review_documentation",
        "requirement_title": "Review and Documentation",
        "group_order": 8,
        "questions": [
            {
                "question_key": "ms_dpa_8_1",
                "question_text": "Who approved this assessment?",
                "guidance": "Document names and positions of approvers.",
                "question_order": 1,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
            {
                "question_key": "ms_dpa_8_2",
                "question_text": "When will this assessment be reviewed?",
                "guidance": "Document review schedule and retention period.",
                "question_order": 2,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
        ],
    },
]


# Best Practice PIA Questions
BEST_PRACTICE_PIA_QUESTIONS = [
    # Group 1: Project Overview
    {
        "requirement_key": "project_overview",
        "requirement_title": "Project Overview",
        "group_order": 1,
        "questions": [
            {
                "question_key": "bp_pia_1_1",
                "question_text": "What is the name and description of this project/processing activity?",
                "guidance": "Provide a clear overview of the project and its business context.",
                "question_order": 1,
                "required": True,
                "fides_sources": ["system.name", "system.description"],
                "expected_coverage": "full",
            },
            {
                "question_key": "bp_pia_1_2",
                "question_text": "What are the purposes of the processing?",
                "guidance": "Describe the business purposes and intended outcomes.",
                "question_order": 2,
                "required": True,
                "fides_sources": ["privacy_declaration.data_use", "data_use.description"],
                "expected_coverage": "full",
            },
            {
                "question_key": "bp_pia_1_3",
                "question_text": "Who is the project owner/sponsor?",
                "guidance": "Identify the accountable individual or team.",
                "question_order": 3,
                "required": True,
                "fides_sources": ["system.administrating_department"],
                "expected_coverage": "partial",
            },
        ],
    },
    # Group 2: Data Inventory
    {
        "requirement_key": "data_inventory",
        "requirement_title": "Data Inventory",
        "group_order": 2,
        "questions": [
            {
                "question_key": "bp_pia_2_1",
                "question_text": "What categories of personal data are processed?",
                "guidance": "List all personal data categories using a standard taxonomy.",
                "question_order": 1,
                "required": True,
                "fides_sources": ["privacy_declaration.data_categories", "data_category.name"],
                "expected_coverage": "full",
            },
            {
                "question_key": "bp_pia_2_2",
                "question_text": "What categories of data subjects are affected?",
                "guidance": "Identify who the data relates to (customers, employees, etc.).",
                "question_order": 2,
                "required": True,
                "fides_sources": ["privacy_declaration.data_subjects"],
                "expected_coverage": "full",
            },
            {
                "question_key": "bp_pia_2_3",
                "question_text": "What is the volume and scale of data processing?",
                "guidance": "Describe the number of individuals, data volume, and geographic scope.",
                "question_order": 3,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
        ],
    },
    # Group 3: Data Flows
    {
        "requirement_key": "data_flows",
        "requirement_title": "Data Flows",
        "group_order": 3,
        "questions": [
            {
                "question_key": "bp_pia_3_1",
                "question_text": "Where does the data come from?",
                "guidance": "Identify all data sources (direct collection, third parties, etc.).",
                "question_order": 1,
                "required": True,
                "fides_sources": ["system.data_flows", "system.ingress"],
                "expected_coverage": "partial",
            },
            {
                "question_key": "bp_pia_3_2",
                "question_text": "Who receives the data?",
                "guidance": "List all recipients including internal teams, processors, and third parties.",
                "question_order": 2,
                "required": True,
                "fides_sources": ["privacy_declaration.third_parties", "system.egress"],
                "expected_coverage": "partial",
            },
            {
                "question_key": "bp_pia_3_3",
                "question_text": "Are there any international data transfers?",
                "guidance": "Identify cross-border transfers and applicable safeguards.",
                "question_order": 3,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
        ],
    },
    # Group 4: Legal Basis
    {
        "requirement_key": "legal_basis",
        "requirement_title": "Legal Basis and Compliance",
        "group_order": 4,
        "questions": [
            {
                "question_key": "bp_pia_4_1",
                "question_text": "What is the legal basis for processing?",
                "guidance": "Identify the applicable legal basis (consent, contract, legitimate interest, etc.).",
                "question_order": 1,
                "required": True,
                "fides_sources": ["privacy_declaration.legal_basis_for_processing"],
                "expected_coverage": "full",
            },
            {
                "question_key": "bp_pia_4_2",
                "question_text": "How is data quality and accuracy ensured?",
                "guidance": "Describe measures to keep data accurate and up-to-date.",
                "question_order": 2,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
            {
                "question_key": "bp_pia_4_3",
                "question_text": "What is the data retention period?",
                "guidance": "Specify how long data is kept and the justification.",
                "question_order": 3,
                "required": True,
                "fides_sources": ["privacy_declaration.retention_period"],
                "expected_coverage": "partial",
            },
        ],
    },
    # Group 5: Risk Assessment
    {
        "requirement_key": "risk_assessment",
        "requirement_title": "Risk Assessment",
        "group_order": 5,
        "questions": [
            {
                "question_key": "bp_pia_5_1",
                "question_text": "What are the privacy risks to individuals?",
                "guidance": "Identify potential harms including financial, reputational, physical, or emotional harm.",
                "question_order": 1,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
            {
                "question_key": "bp_pia_5_2",
                "question_text": "What is the likelihood and severity of each risk?",
                "guidance": "Assess the probability and impact of each identified risk.",
                "question_order": 2,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
            {
                "question_key": "bp_pia_5_3",
                "question_text": "Are there any special category data or vulnerable populations involved?",
                "guidance": "Identify any heightened sensitivity factors.",
                "question_order": 3,
                "required": True,
                "fides_sources": ["privacy_declaration.data_categories", "privacy_declaration.data_subjects"],
                "expected_coverage": "partial",
            },
        ],
    },
    # Group 6: Mitigations
    {
        "requirement_key": "mitigations",
        "requirement_title": "Risk Mitigations",
        "group_order": 6,
        "questions": [
            {
                "question_key": "bp_pia_6_1",
                "question_text": "What technical safeguards are in place?",
                "guidance": "Document security measures (encryption, access controls, etc.).",
                "question_order": 1,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
            {
                "question_key": "bp_pia_6_2",
                "question_text": "What organizational safeguards are in place?",
                "guidance": "Document policies, training, and procedural controls.",
                "question_order": 2,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
            {
                "question_key": "bp_pia_6_3",
                "question_text": "What is the residual risk level after mitigations?",
                "guidance": "Assess remaining risk and whether it is acceptable.",
                "question_order": 3,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
        ],
    },
    # Group 7: Individual Rights
    {
        "requirement_key": "individual_rights",
        "requirement_title": "Individual Rights",
        "group_order": 7,
        "questions": [
            {
                "question_key": "bp_pia_7_1",
                "question_text": "How are individuals informed about the processing?",
                "guidance": "Describe privacy notices and transparency measures.",
                "question_order": 1,
                "required": True,
                "fides_sources": ["privacy_notice.name", "privacy_notice.data_uses"],
                "expected_coverage": "partial",
            },
            {
                "question_key": "bp_pia_7_2",
                "question_text": "How can individuals exercise their rights?",
                "guidance": "Describe mechanisms for access, correction, deletion, and other rights requests.",
                "question_order": 2,
                "required": True,
                "fides_sources": ["privacy_experience", "policy.drp_action"],
                "expected_coverage": "partial",
            },
        ],
    },
    # Group 8: Governance
    {
        "requirement_key": "governance",
        "requirement_title": "Governance and Approval",
        "group_order": 8,
        "questions": [
            {
                "question_key": "bp_pia_8_1",
                "question_text": "Who is accountable for this processing?",
                "guidance": "Identify the data owner and privacy point of contact.",
                "question_order": 1,
                "required": True,
                "fides_sources": ["system.data_stewards"],
                "expected_coverage": "partial",
            },
            {
                "question_key": "bp_pia_8_2",
                "question_text": "Who has reviewed and approved this PIA?",
                "guidance": "Document approvers, dates, and any conditions.",
                "question_order": 2,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
            {
                "question_key": "bp_pia_8_3",
                "question_text": "When and how will this PIA be reviewed?",
                "guidance": "Establish a review schedule and triggers for reassessment.",
                "question_order": 3,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
        ],
    },
]


# Mapping of template keys to their questions
TEMPLATE_QUESTIONS = {
    "uk_gdpr_dpia": UK_GDPR_DPIA_QUESTIONS,
    "us_co_cpa_dpa": COLORADO_CPA_DPA_QUESTIONS,
    "us_va_vcdpa_dpa": VIRGINIA_VCDPA_DPA_QUESTIONS,
    "us_multi_state_dpa": US_MULTI_STATE_DPA_QUESTIONS,
    "best_practice_pia": BEST_PRACTICE_PIA_QUESTIONS,
}


def upgrade() -> None:
    conn = op.get_bind()
    now = datetime.now(timezone.utc)

    for template_data in ASSESSMENT_TEMPLATES:
        # Check if template already exists
        result = conn.execute(
            sa.text("SELECT id FROM assessment_template WHERE key = :key"),
            {"key": template_data["key"]},
        )
        row = result.fetchone()

        if row:
            print(f"Template {template_data['key']} already exists, skipping")
            template_id = row[0]
        else:
            # Create the template
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
            print(f"Created template: {template_data['key']}")

        # Check if questions already exist
        result = conn.execute(
            sa.text(
                "SELECT COUNT(*) FROM assessment_question WHERE template_id = :template_id"
            ),
            {"template_id": template_id},
        )
        count = result.fetchone()[0]
        if count > 0:
            print(f"Template {template_data['key']} already has {count} questions, skipping")
            continue

        # Get questions for this template
        questions_data = TEMPLATE_QUESTIONS.get(template_data["key"])
        if not questions_data:
            print(f"No questions defined for {template_data['key']}")
            continue

        # Seed questions
        question_count = 0
        for group in questions_data:
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

        print(f"Seeded {question_count} questions for {template_data['key']}")


def downgrade() -> None:
    conn = op.get_bind()

    for template_data in ASSESSMENT_TEMPLATES:
        # Find the template
        result = conn.execute(
            sa.text("SELECT id FROM assessment_template WHERE key = :key"),
            {"key": template_data["key"]},
        )
        row = result.fetchone()

        if row:
            template_id = row[0]
            # Delete questions first
            conn.execute(
                sa.text("DELETE FROM assessment_question WHERE template_id = :template_id"),
                {"template_id": template_id},
            )
            # Delete template
            conn.execute(
                sa.text("DELETE FROM assessment_template WHERE id = :id"),
                {"id": template_id},
            )
            print(f"Deleted template and questions for {template_data['key']}")
