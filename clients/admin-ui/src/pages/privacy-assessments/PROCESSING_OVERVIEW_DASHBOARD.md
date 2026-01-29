# Processing Overview Dashboard

## Overview

The "Processing Overview" dashboard is located in Section 2 ("Describe the processing") of the privacy assessment detail page. It provides a quick visual snapshot of the data processing being assessed.

## What the Dashboard Shows

The dashboard displays three summary cards:

### 1. SCOPE

- **What it shows**: Categories of personal data being processed
- **Current example**: "2 Categories Identified" with tags "PII" and "Behavioral Data"
- **Purpose**: Identifies what types of data are involved in the processing activity

### 2. NATURE

- **What it shows**: How the data is being processed
- **Current example**: "AI Analysis" / "Automated Processing"
- **Purpose**: Describes the operations performed on the data (automated, manual, AI-based, etc.)

### 3. CONTEXT

- **What it shows**: The relationship context with data subjects
- **Current example**: "External" / "Customer Facing"
- **Purpose**: Describes the relationship between the organization and data subjects

## Regulatory Alignment

This dashboard aligns with **GDPR Article 35 DPIA requirements**. When conducting a Data Protection Impact Assessment, you must describe:

- The **scope** of processing (what data, how much, how long retained)
- The **nature** of processing (what operations are performed)
- The **context** of processing (relationship with data subjects, their expectations)

The dashboard gives assessors an "at-a-glance" summary before diving into the detailed form fields below.

## Current Implementation Status

**Status: Hardcoded/Prototype**

The dashboard values are currently hardcoded in the UI (see `[id].tsx` lines 1863-1988). This is a UI prototype showing the intended design.

## Data Sources for Dynamic Population

The page already has data structures that could feed this dashboard:

### 1. Document Content State (`documentContent`)

The editable text fields contain scope/nature/context descriptions:

```typescript
{
  scope: "Names, email addresses, IP addresses, purchase history, and clickstream data.",
  nature: "The system uses machine learning algorithms to analyze customer purchase history...",
  context: "Data subjects are existing customers who have opted-in to marketing communications..."
}
```

### 2. Evidence Data (`allEvidence`)

Structured evidence from various sources:

```typescript
{
  id: "sys-1",
  type: "system",
  subtype: "data-classification",
  content: "PII, Behavioral Data",
  source: { system: "Fides Data Map" },
  confidence: 98
}
```

## Future Implementation Options

To make the dashboard dynamic, consider:

1. **Parse from form fields**: Extract key terms from `documentContent.scope`, `documentContent.nature`, `documentContent.context`

2. **Pull from Fides systems**: Use data classification from the Data Map, system inventory, and policy documents

3. **AI-assisted extraction**: Use the analysis evidence type to extract and summarize key characteristics

4. **User selection**: Allow users to select/tag the relevant categories, nature, and context during assessment

## File Location

- **Dashboard code**: `clients/admin-ui/src/pages/privacy-assessments/[id].tsx` (lines 1863-2019)
- **Data state**: Same file, lines 233-266 (`documentContent`)
- **Evidence data**: Same file, lines 279-372 (`allEvidence`)
