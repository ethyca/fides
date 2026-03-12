# EU AI Act FRIA Assessment Template

## Overview

Add a new privacy assessment template for the EU AI Act Fundamental Rights Impact Assessment (FRIA) per Article 27. This template enables deployers of high-risk AI systems to assess and document the impact on fundamental rights before deployment.

## Approach

Single Alembic migration that seeds the `assessment_template` and `assessment_question` tables. No code changes needed: the existing template-driven architecture (executor, frontend, API) automatically picks up the new template.

## Template Metadata

| Field | Value |
|-------|-------|
| key | `eu_ai_act_fria` |
| version | `EU-AIA-FRIA-2024-08-01` |
| name | EU AI Act Fundamental Rights Impact Assessment |
| assessment_type | `eu_ai_act_fria` |
| region | European Union |
| authority | European Commission / EU AI Office |
| legal_reference | EU AI Act (Regulation 2024/1689), Article 27 |
| description | Fundamental rights impact assessment required for deployers of high-risk AI systems under the EU AI Act. |
| is_active | true |

## Question Groups

17 questions across 6 requirement groups, mapped 1:1 to Article 27 obligations.

### Group 1: Process and Purpose (`process_and_purpose`, order: 1)

| Key | Question | Guidance | fides_sources | Coverage |
|-----|----------|----------|---------------|----------|
| `fria_1_1` | What is the name and description of the high-risk AI system being deployed? | Identify the AI system by its commercial name, version, and the AI provider. Include the intended purpose as stated in the provider's instructions for use. | `["system.name", "system.description"]` | `partial` |
| `fria_1_2` | What are the specific business or operational processes in which this AI system will be used? | Describe the exact workflows where the AI is integrated and what decisions it informs. Reference the intended purpose defined by the AI provider. | `["privacy_declaration.name", "privacy_declaration.data_use"]` | `partial` |
| `fria_1_3` | What categories of personal data are processed by the AI system? | List all categories of personal data used as inputs to or generated as outputs by the AI system, including any special category data under GDPR Article 9. | `["data_category.name"]` | `full` |

### Group 2: Duration and Frequency (`duration_and_frequency`, order: 2)

| Key | Question | Guidance | fides_sources | Coverage |
|-----|----------|----------|---------------|----------|
| `fria_2_1` | What is the intended period of deployment for this AI system? | Specify whether this is a permanent deployment, a fixed-term pilot, or a time-limited use. Include start and expected end dates where applicable. | `[]` | `none` |
| `fria_2_2` | How frequently will the AI system be used and in what operational pattern? | Describe whether the system runs continuously (24/7), on a scheduled basis (e.g., batch processing), on-demand, or during specific periods (e.g., annual reviews). | `[]` | `none` |

### Group 3: Affected Populations (`affected_populations`, order: 3)

| Key | Question | Guidance | fides_sources | Coverage |
|-----|----------|----------|---------------|----------|
| `fria_3_1` | What categories of natural persons and groups are likely to be affected by the AI system? | Identify all individuals the AI will interact with, evaluate, or make decisions about, both directly and indirectly. | `["data_subject.name"]` | `partial` |
| `fria_3_2` | Are any vulnerable or historically marginalized groups among the affected populations? | Assess whether the AI may affect people based on protected characteristics (race, age, gender, disability, socioeconomic status, etc.) who could be disproportionately impacted. | `[]` | `none` |
| `fria_3_3` | What is the estimated scale of affected individuals? | Provide an estimate of how many people will be subject to the AI system's outputs, broken down by affected group where possible. | `[]` | `none` |

### Group 4: Risk Identification (`risk_identification`, order: 4)

| Key | Question | Guidance | fides_sources | Coverage |
|-----|----------|----------|---------------|----------|
| `fria_4_1` | What specific risks of harm to fundamental rights have been identified? | Evaluate how the AI could infringe upon rights in the EU Charter of Fundamental Rights, including non-discrimination (Art. 21), privacy (Art. 7-8), human dignity (Art. 1), freedom of expression (Art. 11), and access to justice (Art. 47). Base your analysis on the technical documentation provided by the AI provider. | `[]` | `none` |
| `fria_4_2` | What is the likelihood and severity of each identified risk? | For each risk, assess how probable it is that the harm materializes and how serious the impact would be on affected individuals. Consider both individual and collective harms. | `[]` | `none` |
| `fria_4_3` | Are there risks of bias or discriminatory outcomes in the AI system's outputs? | Analyze whether the system's training data, design, or deployment context could lead to biased or discriminatory results, particularly for the vulnerable groups identified. Reference the AI provider's bias testing documentation. | `[]` | `none` |

### Group 5: Human Oversight (`human_oversight`, order: 5)

| Key | Question | Guidance | fides_sources | Coverage |
|-----|----------|----------|---------------|----------|
| `fria_5_1` | What human oversight measures are in place for this AI system? | Describe who monitors the system, their qualifications, and the frequency of oversight. Reference the human oversight instructions provided by the AI provider per Article 14. | `[]` | `none` |
| `fria_5_2` | What authority do human overseers have to intervene in or override the AI's decisions? | Detail the mechanisms for overriding, reversing, or halting the AI's outputs. Explain at what points human review occurs and whether the AI can act autonomously. | `[]` | `none` |
| `fria_5_3` | What training is provided to prevent automation bias among human overseers? | Describe training programs to ensure overseers critically evaluate AI outputs rather than defaulting to automated recommendations. | `[]` | `none` |

### Group 6: Mitigation and Governance (`mitigation_and_governance`, order: 6)

| Key | Question | Guidance | fides_sources | Coverage |
|-----|----------|----------|---------------|----------|
| `fria_6_1` | What measures will be taken if identified risks materialize? | Detail incident response protocols, including how the AI system can be halted, how affected individuals will be notified, and what remediation steps will follow. | `[]` | `none` |
| `fria_6_2` | What internal governance arrangements are in place for this AI system? | Describe the organizational structure responsible for AI governance, including roles, escalation paths, and review cadences. | `[]` | `none` |
| `fria_6_3` | What complaint mechanisms are available to individuals affected by the AI system? | Describe how affected individuals can challenge the AI's decisions, submit complaints, and seek redress. Include both internal complaint processes and external reporting channels. | `[]` | `none` |

## Implementation

Single Alembic migration file in `src/fides/api/alembic/migrations/versions/`. Follows the established pattern:

1. Define template metadata dict and question groups list as module-level constants
2. `upgrade()`: Insert template row into `assessment_template`, then insert all question rows into `assessment_question` with idempotent checks
3. `downgrade()`: Delete questions by `template_id`, then delete template by `key`
4. Use `generate_id("ast")` / `generate_id("asq")` for prefixed UUIDs
5. All questions are `required: true`

No changes to:
- Models (template-driven, no new columns)
- Services (generic executor handles any template)
- Frontend (templates auto-populate in GenerateAssessmentsModal)
- Schemas or routes

## Testing

- Migration upgrade/downgrade test (verify rows created and removed)
- Verify template appears in `GET /templates` after migration
- Verify questions are returned grouped by requirement with correct ordering
