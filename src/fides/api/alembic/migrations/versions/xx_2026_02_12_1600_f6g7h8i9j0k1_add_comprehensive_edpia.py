"""add Comprehensive Ethyca DPIA (EDPIA) template

This migration adds a comprehensive, de-duplicated privacy impact assessment template
that covers all requirements from:
- GDPR DPIA (Article 35, EDPB WP248)
- UK GDPR DPIA (ICO guidance, Age Appropriate Design Code)
- California CPRA Risk Assessment (CPPA Section 7150)
- Colorado CPA DPA (C.R.S. § 6-1-1309, 4 CCR 904-3)
- Virginia VCDPA DPA (Va. Code Ann. § 59.1-580)
- US Multi-State DPA requirements
- Best Practice PIA (ISO 29134, CNIL, NIST)

Questions are de-duplicated so the same information is only collected once,
with guidance referencing all applicable frameworks.

Revision ID: f6g7h8i9j0k1
Revises: 4d64174f422e
Create Date: 2026-02-12 16:00:00.000000

"""

import uuid
from datetime import datetime, timezone

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "f6g7h8i9j0k1"
down_revision = "4d64174f422e"
branch_labels = None
depends_on = None


def generate_id(prefix: str) -> str:
    """Generate a prefixed UUID."""
    return f"{prefix}_{uuid.uuid4()}"


# Comprehensive EDPIA Template
EDPIA_TEMPLATE = {
    "key": "ethyca_comprehensive_dpia",
    "version": "EDPIA-2024-01",
    "name": "Comprehensive Ethyca DPIA (EDPIA)",
    "assessment_type": "edpia",
    "region": "Global (Multi-Jurisdiction)",
    "authority": "Ethyca - Based on GDPR, UK GDPR, CPRA, CPA, VCDPA, and Best Practices",
    "legal_reference": "GDPR Art. 35, UK GDPR, ICO Guidance, CPPA §7150, C.R.S. §6-1-1309, Va. Code §59.1-580, ISO 29134",
    "description": "A comprehensive, de-duplicated privacy impact assessment that satisfies requirements across GDPR, UK GDPR, US state privacy laws (CA, CO, VA, CT), and industry best practices. Complete this single assessment to demonstrate compliance across multiple jurisdictions.",
    "is_active": True,
}


# Comprehensive EDPIA Questions - De-duplicated and organized by theme
EDPIA_QUESTIONS = [
    # =============================================================================
    # GROUP 1: PROCESSING OVERVIEW
    # Sources: All frameworks require basic processing description
    # =============================================================================
    {
        "requirement_key": "processing_overview",
        "requirement_title": "Processing Overview",
        "group_order": 1,
        "questions": [
            {
                "question_key": "edpia_1_1",
                "question_text": "What is the name and description of this processing activity?",
                "guidance": "Provide a clear, concise description of the processing operations. [GDPR Art. 35(7)(a): 'systematic description'; CPRA: 'processing scope'; All US states: processing description required]",
                "question_order": 1,
                "required": True,
                "fides_sources": ["system.name", "system.description", "privacy_declaration.name"],
                "expected_coverage": "full",
            },
            {
                "question_key": "edpia_1_2",
                "question_text": "What are the specific purposes for this processing?",
                "guidance": "List all purposes/data uses. Be specific about business objectives and intended outcomes. [GDPR Art. 35(7)(a): 'purposes of the processing'; CPRA: 'specific purposes'; All frameworks require purpose specification]",
                "question_order": 2,
                "required": True,
                "fides_sources": ["privacy_declaration.data_use", "data_use.name", "data_use.description"],
                "expected_coverage": "full",
            },
            {
                "question_key": "edpia_1_3",
                "question_text": "Why is this processing necessary for the stated purposes?",
                "guidance": "Explain business necessity and why less intrusive alternatives are insufficient. [GDPR Art. 35(7)(b): 'necessity and proportionality'; CPRA: 'why processing is needed'; CO CPA: 'benefits to controller']",
                "question_order": 3,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
            {
                "question_key": "edpia_1_4",
                "question_text": "What is the nature, scope, and context of the processing?",
                "guidance": "Describe how data is collected, used, stored, and deleted. Include volume, frequency, geographic scope, and relationship with data subjects. [GDPR/UK: 'nature, scope, context'; ICO: Step 2 of DPIA process; CO CPA 4 CCR 904-3-8.04: 'context including controller-consumer relationships']",
                "question_order": 4,
                "required": True,
                "fides_sources": ["system.system_type", "system.administrating_department"],
                "expected_coverage": "partial",
            },
            {
                "question_key": "edpia_1_5",
                "question_text": "Who is the project/processing owner and who is accountable?",
                "guidance": "Identify the accountable individual, team, or department. [Best Practice: ISO 29134 governance; GDPR: controller accountability]",
                "question_order": 5,
                "required": True,
                "fides_sources": ["system.data_stewards", "system.administrating_department"],
                "expected_coverage": "partial",
            },
        ],
    },
    # =============================================================================
    # GROUP 2: DATA INVENTORY
    # Sources: All frameworks require data categories and subjects
    # =============================================================================
    {
        "requirement_key": "data_inventory",
        "requirement_title": "Data Inventory",
        "group_order": 2,
        "questions": [
            {
                "question_key": "edpia_2_1",
                "question_text": "What categories of personal data are processed?",
                "guidance": "List all personal data categories using standardized taxonomy. [GDPR Art. 35(7)(a): 'categories of data'; CPRA: 'categories of personal information'; All US states require this]",
                "question_order": 1,
                "required": True,
                "fides_sources": ["privacy_declaration.data_categories", "data_category.name"],
                "expected_coverage": "full",
            },
            {
                "question_key": "edpia_2_2",
                "question_text": "Does the processing involve sensitive/special category data?",
                "guidance": "Identify any: health, genetic, biometric, racial/ethnic origin, political opinions, religious beliefs, trade union membership, sex life/orientation, criminal data, children's data, financial data, precise geolocation. [GDPR Art. 9: 'special categories'; CPRA: 'sensitive personal information'; All US states have sensitive data definitions]",
                "question_order": 2,
                "required": True,
                "fides_sources": ["privacy_declaration.data_categories"],
                "expected_coverage": "full",
            },
            {
                "question_key": "edpia_2_3",
                "question_text": "What categories of data subjects are affected?",
                "guidance": "Identify who the data relates to: customers, employees, children, patients, website visitors, etc. [GDPR: 'categories of data subjects'; VA VCDPA §59.1-580: 'categories of consumers'; All frameworks]",
                "question_order": 3,
                "required": True,
                "fides_sources": ["privacy_declaration.data_subjects"],
                "expected_coverage": "full",
            },
            {
                "question_key": "edpia_2_4",
                "question_text": "What is the volume and scale of data processing?",
                "guidance": "Estimate: number of individuals affected, data volume, frequency of processing, geographic coverage. [GDPR: 'large scale' is a DPIA trigger; ICO: 'scope' assessment; CO CPA: 'nature and operational elements']",
                "question_order": 4,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
        ],
    },
    # =============================================================================
    # GROUP 3: LEGAL BASIS AND COMPLIANCE
    # Sources: GDPR/UK require legal basis; US states require lawful processing
    # =============================================================================
    {
        "requirement_key": "legal_basis",
        "requirement_title": "Legal Basis and Compliance",
        "group_order": 3,
        "questions": [
            {
                "question_key": "edpia_3_1",
                "question_text": "What is the lawful basis for processing?",
                "guidance": "For GDPR/UK: identify Art. 6 basis (consent, contract, legal obligation, vital interests, public task, legitimate interests). For US: identify applicable legal permissions. [GDPR Art. 6; UK GDPR Art. 6; For legitimate interests, document the balancing test]",
                "question_order": 1,
                "required": True,
                "fides_sources": ["privacy_declaration.legal_basis_for_processing"],
                "expected_coverage": "full",
            },
            {
                "question_key": "edpia_3_2",
                "question_text": "If processing special category data, what is the additional legal basis?",
                "guidance": "For GDPR/UK Art. 9: identify condition (explicit consent, employment law, vital interests, etc.). For US: identify applicable sensitive data permissions. [GDPR Art. 9; CPRA SPI requirements]",
                "question_order": 2,
                "required": False,
                "fides_sources": ["privacy_declaration.special_category_legal_basis"],
                "expected_coverage": "partial",
            },
            {
                "question_key": "edpia_3_3",
                "question_text": "How is data quality and accuracy ensured?",
                "guidance": "Describe measures to keep data accurate, complete, and up-to-date. [GDPR Art. 5(1)(d): accuracy principle; Best practice: data quality controls]",
                "question_order": 3,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
            {
                "question_key": "edpia_3_4",
                "question_text": "How is data minimization achieved?",
                "guidance": "Explain how data collection is limited to what is necessary. Could the purpose be achieved with less data? [GDPR Art. 5(1)(c): data minimisation; CPRA: necessity requirement]",
                "question_order": 4,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
        ],
    },
    # =============================================================================
    # GROUP 4: DATA FLOWS AND RECIPIENTS
    # Sources: All frameworks require disclosure of data sharing
    # =============================================================================
    {
        "requirement_key": "data_flows",
        "requirement_title": "Data Flows and Recipients",
        "group_order": 4,
        "questions": [
            {
                "question_key": "edpia_4_1",
                "question_text": "Where does the personal data come from?",
                "guidance": "Identify all data sources: direct collection, third parties, public sources, inferred/derived data. [Best Practice: data flow mapping; GDPR Art. 14: data not obtained from subject]",
                "question_order": 1,
                "required": True,
                "fides_sources": ["system.ingress"],
                "expected_coverage": "partial",
            },
            {
                "question_key": "edpia_4_2",
                "question_text": "Who receives the personal data and for what purpose?",
                "guidance": "List all recipients: internal teams, processors, joint controllers, third parties. Include purpose of each disclosure. [GDPR Art. 35(7)(a): 'recipients'; CPRA: 'third-party recipients'; VA VCDPA: 'recipients and sale/sharing']",
                "question_order": 2,
                "required": True,
                "fides_sources": ["privacy_declaration.third_parties", "system.egress", "connection.name"],
                "expected_coverage": "partial",
            },
            {
                "question_key": "edpia_4_3",
                "question_text": "Is personal data sold or shared for advertising purposes?",
                "guidance": "Identify if data is: sold (CCPA definition), shared for cross-context behavioral advertising (CPRA), or used for targeted advertising (US state laws). [CPRA: 'selling'/'sharing'; CO/VA/CT: targeted advertising trigger]",
                "question_order": 3,
                "required": True,
                "fides_sources": ["privacy_declaration.data_use"],
                "expected_coverage": "partial",
            },
            {
                "question_key": "edpia_4_4",
                "question_text": "Are there any international/cross-border data transfers?",
                "guidance": "Identify transfers outside: EEA (GDPR), UK (UK GDPR), or to jurisdictions without adequate protection. [GDPR Chapter V; UK: international transfer rules; Include transfer mechanism: adequacy, SCCs, BCRs]",
                "question_order": 4,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
            {
                "question_key": "edpia_4_5",
                "question_text": "What safeguards are in place for international transfers?",
                "guidance": "Document transfer mechanisms and supplementary measures. [GDPR Art. 46: appropriate safeguards; UK: UK SCCs/UK Addendum; Include Transfer Impact Assessment if applicable]",
                "question_order": 5,
                "required": False,
                "fides_sources": [],
                "expected_coverage": "none",
            },
        ],
    },
    # =============================================================================
    # GROUP 5: DATA RETENTION
    # Sources: All frameworks require retention limitation
    # =============================================================================
    {
        "requirement_key": "data_retention",
        "requirement_title": "Data Retention",
        "group_order": 5,
        "questions": [
            {
                "question_key": "edpia_5_1",
                "question_text": "What is the retention period for personal data?",
                "guidance": "Specify retention periods for each data category, or criteria for determining retention. [GDPR Art. 5(1)(e): storage limitation; CPRA: retention periods required; All frameworks]",
                "question_order": 1,
                "required": True,
                "fides_sources": ["privacy_declaration.retention_period"],
                "expected_coverage": "partial",
            },
            {
                "question_key": "edpia_5_2",
                "question_text": "What is the justification for this retention period?",
                "guidance": "Explain the legal or business necessity for the retention period. [CPRA: 'legal or business justification'; Best Practice: retention schedules]",
                "question_order": 2,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
            {
                "question_key": "edpia_5_3",
                "question_text": "How is data deleted or anonymized at end of retention?",
                "guidance": "Describe deletion procedures and verification methods. [GDPR: erasure requirements; Best Practice: secure deletion]",
                "question_order": 3,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
        ],
    },
    # =============================================================================
    # GROUP 6: AUTOMATED DECISION-MAKING AND PROFILING
    # Sources: GDPR Art. 22, CPRA ADMT, CO/VA profiling triggers
    # =============================================================================
    {
        "requirement_key": "automated_decisions",
        "requirement_title": "Automated Decision-Making and Profiling",
        "group_order": 6,
        "questions": [
            {
                "question_key": "edpia_6_1",
                "question_text": "Does this processing involve automated decision-making or profiling?",
                "guidance": "Identify any: profiling, scoring, AI/ML decisions, automated recommendations that affect individuals. [GDPR Art. 22: ADM with legal/significant effects; CPRA: ADMT; CO CPA: profiling triggers; VA VCDPA: profiling]",
                "question_order": 1,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
            {
                "question_key": "edpia_6_2",
                "question_text": "If ADMT/profiling is used, describe the logic and how it works.",
                "guidance": "Provide plain language explanation of the automated logic, factors considered, and how decisions are reached. [GDPR Art. 13-14: 'meaningful information about logic'; CPPA §7150: 'logic of the ADMT'; CO CPA 4 CCR 904-3-9.06: 'plain language explanation']",
                "question_order": 2,
                "required": False,
                "fides_sources": [],
                "expected_coverage": "none",
            },
            {
                "question_key": "edpia_6_3",
                "question_text": "What outputs does the ADMT generate and how are they used?",
                "guidance": "Describe outputs (scores, classifications, recommendations) and their role in decisions affecting individuals. [CPPA §7150: 'outputs generated'; 'how outputs used to make significant decisions']",
                "question_order": 3,
                "required": False,
                "fides_sources": [],
                "expected_coverage": "none",
            },
            {
                "question_key": "edpia_6_4",
                "question_text": "What safeguards exist for automated decisions?",
                "guidance": "Describe human review, ability to contest decisions, bias testing, and fairness measures. [GDPR Art. 22(3): safeguards; CPRA: ADMT safeguards; CO: bias testing requirements]",
                "question_order": 4,
                "required": False,
                "fides_sources": [],
                "expected_coverage": "none",
            },
        ],
    },
    # =============================================================================
    # GROUP 7: RISK ASSESSMENT
    # Sources: All frameworks require risk identification
    # =============================================================================
    {
        "requirement_key": "risk_assessment",
        "requirement_title": "Risk Assessment",
        "group_order": 7,
        "questions": [
            {
                "question_key": "edpia_7_1",
                "question_text": "What risks does this processing pose to individuals' rights and freedoms?",
                "guidance": "Identify potential harms: discrimination, identity theft, financial loss, reputational damage, physical harm, psychological harm, loss of confidentiality, chilling effects. [GDPR Art. 35(7)(c): 'risks to rights and freedoms'; CO CPA 4 CCR 904-3-8.04(6): 11 risk categories; All frameworks]",
                "question_order": 1,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
            {
                "question_key": "edpia_7_2",
                "question_text": "Could this processing result in discrimination or unfair treatment?",
                "guidance": "Assess risk of discriminatory outcomes, disparate impact on protected groups, or unfair/deceptive treatment. [CPPA: 'unlawful discrimination'; CO CPA: 'unfair or deceptive treatment', 'unlawful disparate impact'; VA VCDPA: same]",
                "question_order": 2,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
            {
                "question_key": "edpia_7_3",
                "question_text": "Could this processing result in financial, physical, or reputational harm?",
                "guidance": "Assess tangible harms to individuals. [All US states: 'financial, physical, or reputational injury'; GDPR: 'physical, material or non-material damage']",
                "question_order": 3,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
            {
                "question_key": "edpia_7_4",
                "question_text": "What is the likelihood and severity of each identified risk?",
                "guidance": "For each risk, assess: probability (remote, possible, probable) and severity (minimal, significant, severe). [ICO: likelihood × severity matrix; GDPR Recital 76: consider likelihood and severity; All frameworks]",
                "question_order": 4,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
            {
                "question_key": "edpia_7_5",
                "question_text": "Could this processing involve coercion, manipulation, or dark patterns?",
                "guidance": "Assess whether design could manipulate individuals into sharing more data or making choices against their interests. [CPPA: 'coercion or dark patterns'; Best Practice: ethical design]",
                "question_order": 5,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
        ],
    },
    # =============================================================================
    # GROUP 8: RISK MITIGATION
    # Sources: All frameworks require safeguards
    # =============================================================================
    {
        "requirement_key": "risk_mitigation",
        "requirement_title": "Risk Mitigation Measures",
        "group_order": 8,
        "questions": [
            {
                "question_key": "edpia_8_1",
                "question_text": "What technical measures protect personal data?",
                "guidance": "Describe: encryption (at rest/in transit), pseudonymization, access controls, security monitoring, backup procedures. [GDPR Art. 35(7)(d): 'safeguards, security measures'; CPRA: 'technical security measures'; CO CPA: 'data security practices per §6-1-1308']",
                "question_order": 1,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
            {
                "question_key": "edpia_8_2",
                "question_text": "What organizational measures protect personal data?",
                "guidance": "Describe: policies, staff training, access management, audit procedures, incident response. [GDPR: organizational measures; ICO: 'organisational measures'; Best Practice]",
                "question_order": 2,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
            {
                "question_key": "edpia_8_3",
                "question_text": "Is de-identified or pseudonymized data used where possible?",
                "guidance": "Document use of privacy-enhancing techniques to reduce risk. [GDPR Recital 28: pseudonymization as safeguard; CO/VA/Multi-State: 'de-identified data' consideration]",
                "question_order": 3,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
            {
                "question_key": "edpia_8_4",
                "question_text": "How do the safeguards address each identified risk?",
                "guidance": "Map each risk to specific mitigating measures. Show how residual risk is reduced to acceptable levels. [ICO: risk-to-measure mapping; All frameworks require demonstrating risk reduction]",
                "question_order": 4,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
            {
                "question_key": "edpia_8_5",
                "question_text": "What is the residual risk level after mitigation measures?",
                "guidance": "Assess remaining risk. If high residual risk remains, consider additional measures or supervisory authority consultation. [GDPR Art. 36: prior consultation if high residual risk; ICO: residual risk assessment]",
                "question_order": 5,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
        ],
    },
    # =============================================================================
    # GROUP 9: BENEFITS VS RISKS
    # Sources: US state laws explicitly require; GDPR proportionality
    # =============================================================================
    {
        "requirement_key": "benefits_vs_risks",
        "requirement_title": "Benefits vs. Risks Analysis",
        "group_order": 9,
        "questions": [
            {
                "question_key": "edpia_9_1",
                "question_text": "What are the benefits of this processing to the organization?",
                "guidance": "Describe business value, operational benefits, and necessity. [CPRA: 'benefits to the business'; CO/VA: 'benefits to the controller'; GDPR: necessity assessment]",
                "question_order": 1,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
            {
                "question_key": "edpia_9_2",
                "question_text": "What are the benefits of this processing to individuals?",
                "guidance": "Describe how data subjects benefit: improved services, personalization, safety, etc. [CPRA: 'benefits to consumers'; CO/VA: 'benefits to the consumer'; GDPR: legitimate interests balancing]",
                "question_order": 2,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
            {
                "question_key": "edpia_9_3",
                "question_text": "What are the benefits to other stakeholders and the public?",
                "guidance": "Consider broader societal benefits: research, public health, safety, innovation. [CO/VA/CT: 'benefits to other stakeholders and the public']",
                "question_order": 3,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
            {
                "question_key": "edpia_9_4",
                "question_text": "Do the benefits outweigh the risks to individuals?",
                "guidance": "Provide reasoned conclusion. For US states: benefits must outweigh risks as mitigated by safeguards. For GDPR: processing must be necessary and proportionate. [CPRA: 'risks outweigh benefits' test; CO CPA §6-1-1309(3); VA VCDPA §59.1-580(C); GDPR Art. 35(7)(b): proportionality]",
                "question_order": 4,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
        ],
    },
    # =============================================================================
    # GROUP 10: TRANSPARENCY AND INDIVIDUAL RIGHTS
    # Sources: All frameworks require transparency and rights
    # =============================================================================
    {
        "requirement_key": "transparency_rights",
        "requirement_title": "Transparency and Individual Rights",
        "group_order": 10,
        "questions": [
            {
                "question_key": "edpia_10_1",
                "question_text": "How are individuals informed about this processing?",
                "guidance": "Describe privacy notices, timing, and delivery method. Include layered/just-in-time notices if used. [GDPR Art. 13-14: transparency; ICO: privacy information; CPRA: 'disclosed to consumers'; All frameworks]",
                "question_order": 1,
                "required": True,
                "fides_sources": ["privacy_notice.name", "privacy_notice.data_uses"],
                "expected_coverage": "partial",
            },
            {
                "question_key": "edpia_10_2",
                "question_text": "How can individuals exercise their privacy rights?",
                "guidance": "Describe mechanisms for: access, correction/rectification, deletion/erasure, restriction, portability, objection, opt-out of sale/sharing, limit use of sensitive data. [GDPR Chapter III; CPRA rights; CO/VA/CT rights; Include response timeframes]",
                "question_order": 2,
                "required": True,
                "fides_sources": ["privacy_experience", "policy.drp_action"],
                "expected_coverage": "partial",
            },
            {
                "question_key": "edpia_10_3",
                "question_text": "How are universal opt-out signals (e.g., GPC) honored?",
                "guidance": "Describe how Global Privacy Control and similar signals are detected and honored where legally required. [CPRA: GPC required; CO CPA: universal opt-out; Several US states require]",
                "question_order": 3,
                "required": True,
                "fides_sources": ["fides.config"],
                "expected_coverage": "partial",
            },
        ],
    },
    # =============================================================================
    # GROUP 11: CHILDREN AND VULNERABLE GROUPS
    # Sources: UK Children's Code, VA children provisions, COPPA
    # =============================================================================
    {
        "requirement_key": "children_vulnerable",
        "requirement_title": "Children and Vulnerable Groups",
        "group_order": 11,
        "questions": [
            {
                "question_key": "edpia_11_1",
                "question_text": "Is the service/processing likely to be accessed by children (under 18)?",
                "guidance": "Consider whether children are part of intended audience or might access regardless. [UK Age Appropriate Design Code: Standard 2; VA VCDPA §59.1-580(B): children's online services; COPPA if under 13]",
                "question_order": 1,
                "required": True,
                "fides_sources": ["privacy_declaration.data_subjects"],
                "expected_coverage": "partial",
            },
            {
                "question_key": "edpia_11_2",
                "question_text": "If children may be affected, what additional safeguards are in place?",
                "guidance": "Consider: best interests of child, age-appropriate defaults, data minimization, parental controls, no harmful nudges. [UK Children's Code: 15 standards; VA: purpose, categories, and purposes for children's data]",
                "question_order": 2,
                "required": False,
                "fides_sources": [],
                "expected_coverage": "none",
            },
            {
                "question_key": "edpia_11_3",
                "question_text": "Does the processing involve other vulnerable individuals?",
                "guidance": "Identify if processing affects: employees (power imbalance), elderly, disabled persons, patients, asylum seekers, or others with restricted ability to consent. [ICO: vulnerable data subjects as high-risk indicator; GDPR: power imbalance consideration]",
                "question_order": 3,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
        ],
    },
    # =============================================================================
    # GROUP 12: CONTRACTUAL SAFEGUARDS
    # Sources: GDPR Art. 28, CPRA contracts, CO contracts
    # =============================================================================
    {
        "requirement_key": "contractual_safeguards",
        "requirement_title": "Contractual Safeguards",
        "group_order": 12,
        "questions": [
            {
                "question_key": "edpia_12_1",
                "question_text": "Do contracts with processors include required data protection provisions?",
                "guidance": "For GDPR/UK: Art. 28 processor agreement requirements. For US: required CCPA/state law provisions restricting use/sale and requiring DSR assistance. [GDPR Art. 28; CPRA service provider contracts; CO CPA: processor agreements]",
                "question_order": 1,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
            {
                "question_key": "edpia_12_2",
                "question_text": "For international transfers, are appropriate contractual mechanisms in place?",
                "guidance": "Document: EU SCCs, UK SCCs/Addendum, BCRs, or other approved mechanisms. [GDPR Art. 46; UK international transfer requirements]",
                "question_order": 2,
                "required": False,
                "fides_sources": [],
                "expected_coverage": "none",
            },
        ],
    },
    # =============================================================================
    # GROUP 13: CONSULTATION
    # Sources: GDPR Art. 35(2), Art. 35(9), Art. 36
    # =============================================================================
    {
        "requirement_key": "consultation",
        "requirement_title": "Consultation",
        "group_order": 13,
        "questions": [
            {
                "question_key": "edpia_13_1",
                "question_text": "Has the Data Protection Officer (DPO) been consulted?",
                "guidance": "Document DPO advice and how it has been addressed. [GDPR Art. 35(2): 'shall seek the advice of the DPO'; UK: DPO consultation required]",
                "question_order": 1,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
            {
                "question_key": "edpia_13_2",
                "question_text": "What specific advice did the DPO provide and how was it addressed?",
                "guidance": "Document recommendations and implementation or reasons for not implementing. [GDPR Art. 35(2); ICO: document DPO advice]",
                "question_order": 2,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
            {
                "question_key": "edpia_13_3",
                "question_text": "Have data subjects or their representatives been consulted?",
                "guidance": "If appropriate, describe consultation with affected individuals, focus groups, or advocacy groups. If not consulted, explain why. [GDPR Art. 35(9): 'seek the views of data subjects'; ICO: consultation requirements]",
                "question_order": 3,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
            {
                "question_key": "edpia_13_4",
                "question_text": "Were external parties consulted (security, legal, AI bias experts)?",
                "guidance": "Document any external consultation, particularly for ADMT processing. If not consulted, explain why. [CPPA §7150: external consultation including AI bias experts; Best Practice: expert review]",
                "question_order": 4,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
            {
                "question_key": "edpia_13_5",
                "question_text": "Is prior consultation with the supervisory authority required?",
                "guidance": "Required if high residual risk remains that cannot be mitigated. For UK: consult ICO. For EU: consult relevant DPA. [GDPR Art. 36; ICO prior consultation process (8-week timeline)]",
                "question_order": 5,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
        ],
    },
    # =============================================================================
    # GROUP 14: APPROVAL AND GOVERNANCE
    # Sources: All frameworks require accountability
    # =============================================================================
    {
        "requirement_key": "approval_governance",
        "requirement_title": "Approval and Governance",
        "group_order": 14,
        "questions": [
            {
                "question_key": "edpia_14_1",
                "question_text": "Who has reviewed and approved this assessment?",
                "guidance": "Document names, roles, positions, and sign-off dates. Include DPO sign-off if applicable. [CO CPA 4 CCR 904-3-8.04: 'names, positions, and signatures'; ICO: sign-off requirements; All frameworks: accountability]",
                "question_order": 1,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
            {
                "question_key": "edpia_14_2",
                "question_text": "Who has accepted the residual risk?",
                "guidance": "Document the accountable decision-maker who accepts any remaining risk. [GDPR: controller accountability; Best Practice: risk acceptance sign-off]",
                "question_order": 2,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
            {
                "question_key": "edpia_14_3",
                "question_text": "Have any internal or external audits been conducted?",
                "guidance": "Document auditor name, scope, and findings. [CO CPA 4 CCR 904-3-8.04: audit documentation; Best Practice: independent review]",
                "question_order": 3,
                "required": False,
                "fides_sources": [],
                "expected_coverage": "none",
            },
        ],
    },
    # =============================================================================
    # GROUP 15: REVIEW AND CHANGE MANAGEMENT
    # Sources: GDPR Art. 35(11), all frameworks
    # =============================================================================
    {
        "requirement_key": "review_management",
        "requirement_title": "Review and Change Management",
        "group_order": 15,
        "questions": [
            {
                "question_key": "edpia_15_1",
                "question_text": "When will this assessment be reviewed?",
                "guidance": "Establish review schedule. For profiling (CO): review at least annually. DPIAs should be reviewed when processing changes. [GDPR Art. 35(11): review when risk changes; CO CPA: annual for profiling; ICO: regular review]",
                "question_order": 1,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
            {
                "question_key": "edpia_15_2",
                "question_text": "What changes would trigger a reassessment?",
                "guidance": "Identify triggers: new data categories, new purposes, increased scale, technology changes, security incidents, regulatory changes, new recipients. [GDPR Art. 35(11); ICO: change triggers]",
                "question_order": 2,
                "required": True,
                "fides_sources": [],
                "expected_coverage": "none",
            },
            {
                "question_key": "edpia_15_3",
                "question_text": "How long will this assessment be retained?",
                "guidance": "Retain for duration of processing plus regulatory requirements. CO: at least 3 years after processing ends. CPRA: 5 years or duration of processing. [CO CPA: 3-year retention; CPPA: 5-year retention]",
                "question_order": 3,
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

    # Check if template already exists
    result = conn.execute(
        sa.text("SELECT id FROM assessment_template WHERE key = :key"),
        {"key": EDPIA_TEMPLATE["key"]},
    )
    row = result.fetchone()

    if row:
        print(f"Template {EDPIA_TEMPLATE['key']} already exists, skipping")
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
                "key": EDPIA_TEMPLATE["key"],
                "version": EDPIA_TEMPLATE["version"],
                "name": EDPIA_TEMPLATE["name"],
                "assessment_type": EDPIA_TEMPLATE["assessment_type"],
                "region": EDPIA_TEMPLATE["region"],
                "authority": EDPIA_TEMPLATE["authority"],
                "legal_reference": EDPIA_TEMPLATE["legal_reference"],
                "description": EDPIA_TEMPLATE["description"],
                "is_active": EDPIA_TEMPLATE["is_active"],
                "created_at": now,
                "updated_at": now,
            },
        )
        print(f"Created template: {EDPIA_TEMPLATE['key']}")

    # Check if questions already exist
    result = conn.execute(
        sa.text(
            "SELECT COUNT(*) FROM assessment_question WHERE template_id = :template_id"
        ),
        {"template_id": template_id},
    )
    count = result.fetchone()[0]
    if count > 0:
        print(f"Template {EDPIA_TEMPLATE['key']} already has {count} questions, skipping")
        return

    # Seed questions
    question_count = 0
    for group in EDPIA_QUESTIONS:
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

    print(f"Seeded {question_count} questions for {EDPIA_TEMPLATE['key']}")


def downgrade() -> None:
    conn = op.get_bind()

    # Find the template
    result = conn.execute(
        sa.text("SELECT id FROM assessment_template WHERE key = :key"),
        {"key": EDPIA_TEMPLATE["key"]},
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
        print(f"Deleted template and questions for {EDPIA_TEMPLATE['key']}")
