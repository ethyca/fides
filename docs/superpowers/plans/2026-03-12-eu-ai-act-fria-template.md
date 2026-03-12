# EU AI Act FRIA Assessment Template Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an EU AI Act Fundamental Rights Impact Assessment (FRIA) template via an Alembic migration, following the established template-driven pattern.

**Architecture:** Single data-only Alembic migration that inserts one `assessment_template` row and 17 `assessment_question` rows. No model, service, frontend, or schema changes needed. The existing generic executor, API routes, and frontend components automatically pick up new templates.

**Tech Stack:** Python, Alembic, SQLAlchemy (raw SQL via `sa.text()`), PostgreSQL

**Spec:** `docs/superpowers/specs/2026-03-12-eu-ai-act-fria-template-design.md`

---

## Chunk 1: Migration

### Task 1: Create the Alembic migration file

**Files:**
- Create: `src/fides/api/alembic/migrations/versions/xx_2026_03_12_1200_<revision>_add_eu_ai_act_fria_template.py`
- Reference: `src/fides/api/alembic/migrations/versions/xx_2026_02_12_1400_d4e5f6g7h8i9_add_remaining_prd_assessments.py` (pattern to follow)

- [ ] **Step 1: Generate the Alembic revision**

```bash
cd /Users/adriangalvan/Documents/Github/fides
python -c "import uuid; print(uuid.uuid4().hex[:12])"
```

Use the output as the revision ID. The `down_revision` is `4ac4864180db` (current head).

- [ ] **Step 2: Write the migration file**

Create `src/fides/api/alembic/migrations/versions/xx_2026_03_12_1200_<revision>_add_eu_ai_act_fria_template.py` with this content:

```python
"""Add EU AI Act FRIA assessment template

Seeds the assessment_template and assessment_question tables with the
EU AI Act Fundamental Rights Impact Assessment (Article 27) template.

Revision ID: <revision>
Revises: 4ac4864180db
Create Date: 2026-03-12 12:00:00.000000

"""

import uuid
from datetime import datetime, timezone

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "<revision>"
down_revision = "4ac4864180db"
branch_labels = None
depends_on = None


def generate_id(prefix: str) -> str:
    """Generate a prefixed UUID."""
    return f"{prefix}_{uuid.uuid4()}"


ASSESSMENT_TEMPLATE = {
    "key": "eu_ai_act_fria",
    "version": "EU-AIA-FRIA-2024-08-01",
    "name": "EU AI Act Fundamental Rights Impact Assessment",
    "assessment_type": "eu_ai_act_fria",
    "region": "European Union",
    "authority": "European Commission / EU AI Office",
    "legal_reference": "EU AI Act (Regulation 2024/1689), Article 27",
    "description": "Fundamental rights impact assessment required for deployers of high-risk AI systems under the EU AI Act.",
    "is_active": True,
}

TEMPLATE_QUESTIONS = [
    {
        "requirement_key": "process_and_purpose",
        "requirement_title": "Process and Purpose",
        "group_order": 1,
        "questions": [
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
                "guidance": "Describe the exact workflows where the AI is integrated and what decisions it informs. Reference the intended purpose defined by the AI provider.",
                "question_order": 2,
                "required": True,
                "fides_sources": ["privacy_declaration.name", "privacy_declaration.data_use"],
                "expected_coverage": "partial",
            },
            {
                "question_key": "fria_1_3",
                "question_text": "What categories of personal data are processed by the AI system?",
                "guidance": "List all categories of personal data used as inputs to or generated as outputs by the AI system, including any special category data under GDPR Article 9.",
                "question_order": 3,
                "required": True,
                "fides_sources": ["privacy_declaration.data_categories", "data_category.name"],
                "expected_coverage": "full",
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
                "guidance": "Provide an estimate of how many people will be subject to the AI system's outputs, broken down by affected group where possible.",
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
                "fides_sources": ["system.data_security_practices"],
                "expected_coverage": "partial",
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
        ],
    },
]


def upgrade() -> None:
    conn = op.get_bind()
    now = datetime.now(timezone.utc)

    # Check if template already exists
    result = conn.execute(
        sa.text("SELECT id FROM assessment_template WHERE key = :key"),
        {"key": ASSESSMENT_TEMPLATE["key"]},
    )
    row = result.fetchone()

    if row:
        print(f"Template {ASSESSMENT_TEMPLATE['key']} already exists, skipping")
        template_id = row[0]
    else:
        template_id = generate_id("ast")
        conn.execute(
            sa.text("""
                INSERT INTO assessment_template (id, key, version, name, assessment_type, region, authority, legal_reference, description, is_active, created_at, updated_at)
                VALUES (:id, :key, :version, :name, :assessment_type, :region, :authority, :legal_reference, :description, :is_active, :created_at, :updated_at)
            """),
            {
                "id": template_id,
                "key": ASSESSMENT_TEMPLATE["key"],
                "version": ASSESSMENT_TEMPLATE["version"],
                "name": ASSESSMENT_TEMPLATE["name"],
                "assessment_type": ASSESSMENT_TEMPLATE["assessment_type"],
                "region": ASSESSMENT_TEMPLATE["region"],
                "authority": ASSESSMENT_TEMPLATE["authority"],
                "legal_reference": ASSESSMENT_TEMPLATE["legal_reference"],
                "description": ASSESSMENT_TEMPLATE["description"],
                "is_active": ASSESSMENT_TEMPLATE["is_active"],
                "created_at": now,
                "updated_at": now,
            },
        )
        print(f"Created template: {ASSESSMENT_TEMPLATE['key']}")

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
            f"Template {ASSESSMENT_TEMPLATE['key']} already has {count} questions, skipping"
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

    print(f"Seeded {question_count} questions for {ASSESSMENT_TEMPLATE['key']}")


def downgrade() -> None:
    conn = op.get_bind()

    result = conn.execute(
        sa.text("SELECT id FROM assessment_template WHERE key = :key"),
        {"key": ASSESSMENT_TEMPLATE["key"]},
    )
    row = result.fetchone()

    if row:
        template_id = row[0]
        conn.execute(
            sa.text(
                "DELETE FROM assessment_question WHERE template_id = :template_id"
            ),
            {"template_id": template_id},
        )
        conn.execute(
            sa.text("DELETE FROM assessment_template WHERE id = :id"),
            {"id": template_id},
        )
        print(f"Deleted template: {ASSESSMENT_TEMPLATE['key']}")
```

- [ ] **Step 3: Run static checks on the migration file**

```bash
nox -s static_checks
```

Expected: PASS (no lint or type errors)

- [ ] **Step 4: Commit the migration**

```bash
git add src/fides/api/alembic/migrations/versions/xx_2026_03_12_1200_*_add_eu_ai_act_fria_template.py
git commit -m "feat: add EU AI Act FRIA assessment template migration"
```

### Task 2: Verify migration works

- [ ] **Step 1: Start the dev environment**

```bash
nox -s dev
```

Wait for it to be ready (migrations run automatically on startup).

- [ ] **Step 2: Verify the template was created**

```bash
CLIENT_ID="${FIDES_ENV__OAUTH_ROOT_CLIENT_ID:-fidesadmin}"
CLIENT_SECRET="${FIDES_ENV__OAUTH_ROOT_CLIENT_SECRET:-fidesadminsecret}"
TOKEN=$(curl -s -X POST "http://localhost:8080/api/v1/oauth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials&client_id=${CLIENT_ID}&client_secret=${CLIENT_SECRET}" \
  | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))")

curl -s "http://localhost:8080/api/v1/plus/privacy-assessments/templates" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

Expected: The response includes a template with `"key": "eu_ai_act_fria"` and `"name": "EU AI Act Fundamental Rights Impact Assessment"`.

- [ ] **Step 3: Verify questions were seeded**

```bash
# Get the template ID from the previous response, then:
curl -s "http://localhost:8080/api/v1/plus/privacy-assessments/templates/<template_id>" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

Expected: 17 questions across 6 requirement groups, with correct `fides_sources` and `expected_coverage` values.

- [ ] **Step 4: Verify the template appears in the Admin UI**

Open `http://localhost:3000` in a browser, log in (`root_user` / `Testpassword1!`), navigate to Privacy Assessments, and click "Generate Assessments". The "EU AI Act Fundamental Rights Impact Assessment" should appear in the assessment type selector.

### Task 3: Add changelog entry

**Files:**
- Create: `changelog/<PR#>-eu-ai-act-fria.yaml`

- [ ] **Step 1: Create the changelog fragment**

```yaml
type: Added
description: Added EU AI Act Fundamental Rights Impact Assessment (FRIA) template for Article 27 compliance
pr: <PR#>
labels: ["db-migration"]
```

- [ ] **Step 2: Commit the changelog**

```bash
git add changelog/<PR#>-eu-ai-act-fria.yaml
git commit -m "changelog: add entry for EU AI Act FRIA template"
```
