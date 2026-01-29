# Evidence Tray API Specification

This document describes the data sources and structures for the Privacy Assessment Evidence Tray. The evidence tray displays system-derived data and human input that supports privacy assessment responses.

## Overview

The evidence tray has two main sections:

1. **System-derived data** - Automated data points extracted from Fides systems
2. **Human input** - Manual entries and stakeholder communications

Each section also includes an AI-generated **Summary** that synthesizes the evidence below it.

---

## System-Derived Data Section

Automated data points extracted from system inventory, classifications, policies, and monitoring systems.

### Source Types

| Subtype               | Source Name      | Description                                      |
|-----------------------|------------------|--------------------------------------------------|
| `data-classification` | Data map         | Field-level and system-level data categories     |
| `system-inventory`    | System inventory | System metadata, privacy flags, legal basis      |
| `data-flow`           | System inventory | System egress/ingress data transfers             |
| `policy-document`     | Policy           | Policy rules, retention periods, masking         |
| `dsr-execution`       | Privacy requests | Privacy request execution logs and statistics    |
| `consent-record`      | Consent          | Consent preferences and opt-in/opt-out rates     |
| `compliance-monitor`  | Evaluations      | Policy evaluations and compliance status         |
| `system-change`       | System history   | Historical changes to system configurations      |

### Source Type Details

#### Data Classification (`data-classification`)

| Property      | Value                                                                 |
|---------------|-----------------------------------------------------------------------|
| Source        | Data map                                                              |
| Description   | Field-level and system-level data categories from Fides taxonomy      |
| Data used     | Data category taxonomy paths (e.g., `user.contact.email`)             |
| Fides tables  | `Dataset`, `DatasetConfig`, `ctl_data_categories`                     |
| Example value | `user.contact.email, user.behavior.browsing_history`                  |

#### System Inventory (`system-inventory`)

| Property      | Value                                                                 |
|---------------|-----------------------------------------------------------------------|
| Source        | System inventory                                                      |
| Description   | System metadata, privacy flags, and legal basis configuration         |
| Data used     | `processes_personal_data`, `uses_profiling`, `legal_basis_for_profiling` |
| Fides tables  | `System` (`ctl_systems`)                                              |
| Example value | `processes_personal_data: true, uses_profiling: true`                 |

#### Data Flow (`data-flow`)

| Property      | Value                                                                 |
|---------------|-----------------------------------------------------------------------|
| Source        | System inventory                                                      |
| Description   | System egress and ingress data transfer configurations                |
| Data used     | Ingress sources, egress destinations, data categories transferred     |
| Fides tables  | `System.ingress`, `System.egress`                                     |
| Example value | `Ingress: Commerce Engine API → Module`                               |

#### Policy (`policy-document`)

| Property      | Value                                                                 |
|---------------|-----------------------------------------------------------------------|
| Source        | Policy                                                                |
| Description   | Policy rules, retention periods, and masking strategies               |
| Data used     | Retention period, erasure rules, target data categories               |
| Fides tables  | `Policy`, `Rule`, `RuleTarget`                                        |
| Example value | `24 months, erasure on request`                                       |

#### DSR Execution (`dsr-execution`)

| Property      | Value                                                                 |
|---------------|-----------------------------------------------------------------------|
| Source        | Privacy requests                                                      |
| Description   | Privacy request execution logs and aggregate statistics               |
| Data used     | Request counts by type, completion times, avg processing duration     |
| Fides tables  | `PrivacyRequest`, `RequestTask`, `ExecutionLog`                       |
| Example value | `12 access requests, 3 erasure requests, avg 4.2 days`                |

#### Consent Record (`consent-record`)

| Property      | Value                                                                 |
|---------------|-----------------------------------------------------------------------|
| Source        | Consent                                                               |
| Description   | Consent preferences and opt-in/opt-out rates by purpose               |
| Data used     | Consent rates by purpose, preference history counts                   |
| Fides tables  | `CurrentPrivacyPreference`, `PrivacyPreferenceHistory`, `PrivacyNotice` |
| Example value | `marketing.profiling: 78% opt-in, functional.service: 95% opt-in`     |

#### Compliance Monitor (`compliance-monitor`)

| Property      | Value                                                                 |
|---------------|-----------------------------------------------------------------------|
| Source        | Evaluations                                                           |
| Description   | Policy evaluations and compliance status                              |
| Data used     | Evaluation results, violations, compliance status                     |
| Fides tables  | `Evaluation` (`ctl_evaluations`)                                      |
| Example value | `Last evaluation: Passed, 0 violations`                               |

#### System Change (`system-change`)

| Property      | Value                                                                 |
|---------------|-----------------------------------------------------------------------|
| Source        | System history                                                        |
| Description   | Historical changes to system configurations (audit trail)             |
| Data used     | Change timestamps, previous values, change author                     |
| Fides tables  | `SystemHistory`                                                       |
| Example value | `uses_profiling changed from false to true on Jan 10, 2024`           |

### Data Structure

```typescript
interface SystemEvidenceItem {
  id: string;
  questionId: string;           // Which assessment question this relates to
  type: "system";
  subtype: SystemSubtype;       // See table above
  summary: string;              // Human-readable summary (e.g., "3 data categories found")
  label: string;                // Label for the value (e.g., "Data categories")
  content: string;              // The actual data/value
  source: {
    system: string;             // Source name (e.g., "Data map", "System inventory")
  };
  timestamp: string;            // ISO 8601 timestamp of last update
  links?: Array<{
    label: string;
    url: string;                // Deep link to source in Fides UI
  }>;
}
```

### Example Payloads

**Data Classification**
```json
{
  "id": "sys-1",
  "questionId": "2",
  "type": "system",
  "subtype": "data-classification",
  "summary": "3 data categories found",
  "label": "Data categories",
  "content": "user.contact.email, user.behavior.browsing_history, user.financial.purchase_history",
  "source": { "system": "Data map" },
  "timestamp": "2024-01-15T14:23:00Z",
  "links": [{ "label": "View in data map", "url": "/data-map/systems/..." }]
}
```

**System Inventory**
```json
{
  "id": "sys-2",
  "questionId": "2",
  "type": "system",
  "subtype": "system-inventory",
  "summary": "Profiling enabled with legitimate interest basis",
  "label": "System configuration",
  "content": "processes_personal_data: true, uses_profiling: true, legal_basis_for_profiling: Legitimate Interest",
  "source": { "system": "System inventory" },
  "timestamp": "2024-01-15T14:20:00Z",
  "links": [{ "label": "View system details", "url": "/systems/..." }]
}
```

**DSR Execution**
```json
{
  "id": "sys-5",
  "questionId": "2",
  "type": "system",
  "subtype": "dsr-execution",
  "summary": "15 requests completed in last 30 days",
  "label": "Request activity (30 days)",
  "content": "12 access requests completed, 3 erasure requests completed, avg 4.2 days",
  "source": { "system": "Privacy requests" },
  "timestamp": "2024-01-15T12:00:00Z",
  "links": [{ "label": "View request logs", "url": "/privacy-requests" }]
}
```

---

## Human Input Section

Manual entries and stakeholder communications that inform the assessment.

### Source Types

| Subtype                      | Description                                          |
|------------------------------|------------------------------------------------------|
| `manual-entry`               | Free-text input entered by assessment participants   |
| `stakeholder-communication`  | Captured Slack/email threads with stakeholders       |

### Source Type Details

#### Manual Entry (`manual-entry`)

| Property      | Value                                                                 |
|---------------|-----------------------------------------------------------------------|
| Description   | Free-text input entered directly by assessment participants           |
| Data used     | Content text, author info, verification status                        |
| Storage       | Assessment responses table                                            |
| Status values | `verified`, `pending-review`, `draft`                                 |
| Example value | "Processing involves ML analysis of customer purchase history..."     |

#### Stakeholder Communication (`stakeholder-communication`)

| Property      | Value                                                                 |
|---------------|-----------------------------------------------------------------------|
| Description   | Captured Slack/email threads with stakeholders for context            |
| Data used     | Thread messages, participants, channel, timestamps                    |
| Storage       | Assessment communications table                                       |
| Channels      | Slack, Email, Teams (future)                                          |
| Example value | "Data flow discussion with team" (4 messages in thread)               |

### Data Structure

```typescript
interface HumanEvidenceItem {
  id: string;
  questionId: string;
  type: "human";
  subtype: "manual-entry" | "stakeholder-communication";
  content: string;              // Entry text or thread title
  source: {
    person: {
      name: string;             // Author name
      role: string;             // Author role (e.g., "Privacy Officer")
    };
  };
  timestamp: string;
  status?: "verified" | "pending-review" | "draft";

  // For stakeholder-communication only:
  channel?: string;             // e.g., "Slack #privacy-assessments"
  participants?: string[];      // List of participant names
  threadMessages?: Array<{
    sender: string;
    timestamp: string;
    message: string;
  }>;
}
```

### Example Payloads

**Manual Entry**
```json
{
  "id": "human-1",
  "questionId": "2",
  "type": "human",
  "subtype": "manual-entry",
  "content": "Processing involves ML analysis of customer purchase history and browsing behavior for personalized recommendations.",
  "source": { "person": { "name": "Jane Smith", "role": "Privacy Officer" } },
  "timestamp": "2024-01-15T14:20:00Z",
  "status": "verified"
}
```

**Stakeholder Communication**
```json
{
  "id": "human-2",
  "questionId": "2",
  "type": "human",
  "subtype": "stakeholder-communication",
  "content": "Data flow discussion with team",
  "source": { "person": { "name": "Jane Smith", "role": "Privacy Officer" } },
  "timestamp": "2024-01-15T14:15:00Z",
  "channel": "Slack #privacy-assessments",
  "participants": ["Jane Smith", "Sarah Johnson", "Data Steward Team"],
  "threadMessages": [
    {
      "sender": "Jane Smith",
      "timestamp": "2024-01-15T14:15:00Z",
      "message": "Can you help me understand the data flow?"
    },
    {
      "sender": "Sarah Johnson",
      "timestamp": "2024-01-15T14:18:00Z",
      "message": "Data is ingested via API from the core commerce engine."
    }
  ]
}
```

---

## AI Summary Section

Each section (system-derived and human input) includes an AI-generated summary that synthesizes the evidence.

### Data Structure

```typescript
interface AnalysisEvidenceItem {
  id: string;
  questionId: string;
  type: "analysis";
  subtype: "summary" | "inference" | "risk-assessment" | "compliance-check";
  section: "system" | "human";  // Which section this summary belongs to
  content: string;              // The synthesized summary text
  source: {
    model: string;              // e.g., "GPT-4-turbo (v2024.01)"
  };
  timestamp: string;
  confidence: number;           // 0-100, displayed as High/Medium/Low
  references: string[];         // IDs of evidence items used to generate summary
}
```

### Confidence Levels

| Confidence % | Display Label |
|--------------|---------------|
| >= 80% | High |
| 50-79% | Medium |
| < 50% | Low |

### Example Payload

```json
{
  "id": "analysis-1",
  "questionId": "2",
  "type": "analysis",
  "subtype": "summary",
  "section": "system",
  "content": "Processing involves ML analysis of customer purchase history and browsing behavior for personalized recommendations. Data from commerce engine, processed in isolated environment. Scope: PII and behavioral data for opted-in customers. 78% consent rate for profiling purposes.",
  "source": { "model": "GPT-4-turbo (v2024.01)" },
  "timestamp": "2024-01-15T15:30:00Z",
  "confidence": 87,
  "references": ["sys-1", "sys-2", "sys-6"]
}
```

---

## Suggested API Endpoints

### GET /api/v1/privacy-assessments/{assessment_id}/evidence

Returns all evidence for an assessment, grouped by question.

**Response:**
```json
{
  "assessment_id": "uuid",
  "evidence_by_question": {
    "2": {
      "system": [...],
      "human": [...]
    }
  }
}
```

### GET /api/v1/privacy-assessments/{assessment_id}/evidence/system

Returns only system-derived evidence for an assessment.

**Query Parameters:**
- `question_id` (optional) - Filter by assessment question
- `subtype` (optional) - Filter by source type (e.g., `data-classification`)

### GET /api/v1/privacy-assessments/{assessment_id}/evidence/human

Returns only human input evidence for an assessment.

**Query Parameters:**
- `question_id` (optional) - Filter by assessment question
- `subtype` (optional) - Filter by type (`manual-entry` or `stakeholder-communication`)

### POST /api/v1/privacy-assessments/{assessment_id}/evidence/human

Create a new human input entry.

**Request Body:**
```json
{
  "question_id": "2",
  "subtype": "manual-entry",
  "content": "...",
  "status": "draft"
}
```

### POST /api/v1/privacy-assessments/{assessment_id}/evidence/generate-summary

Generate AI summary for a section.

**Request Body:**
```json
{
  "question_id": "2",
  "section": "system",
  "evidence_ids": ["sys-1", "sys-2", "sys-3"]
}
```

**Response:**
```json
{
  "id": "analysis-1",
  "content": "...",
  "confidence": 87,
  "model": "GPT-4-turbo (v2024.01)"
}
```

---

## Data Aggregation Requirements

To populate the evidence tray, the backend needs to aggregate data from multiple Fides tables.

### System-Derived Data Sources

| Source Type         | Tables/Models Required                                  |
|---------------------|--------------------------------------------------------|
| Data classification | `Dataset`, `DatasetConfig`, `ctl_data_categories`      |
| System inventory    | `System`                                                |
| Data flows          | `System`                                                |
| Policy              | `Policy`, `Rule`, `RuleTarget`                          |
| DSR execution       | `PrivacyRequest`, `RequestTask`                         |
| Consent             | `CurrentPrivacyPreference`, `PrivacyNotice`             |
| Compliance          | `Evaluation`                                            |
| System history      | `SystemHistory`                                         |

### Aggregation Logic by Source Type

| Source Type         | Aggregation Logic                                       |
|---------------------|--------------------------------------------------------|
| Data classification | Get all data categories associated with the system      |
| System inventory    | Extract privacy flags, legal basis, processing purposes |
| Data flows          | Parse ingress/egress configurations                     |
| Policy              | Get applicable policies and their rules                 |
| DSR execution       | Aggregate request counts and completion metrics         |
| Consent             | Calculate opt-in rates by purpose                       |
| Compliance          | Get latest evaluation status and violations             |
| System history      | Get recent changes to system configuration              |

### Linking Evidence to Assessment Questions

Evidence items should be linked to assessment questions based on relevance:

| Question                  | Relevant Evidence Types                              |
|---------------------------|-----------------------------------------------------|
| Describe the processing   | `data-classification`, `system-inventory`, `data-flow` |
| Legal basis               | `policy-document`, `consent-record`                  |
| Data subject rights       | `dsr-execution`, `policy-document`                   |
| Risk assessment           | `compliance-monitor`, `system-change`                |
