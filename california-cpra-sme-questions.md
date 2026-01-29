# California CPRA Risk Assessment - SME Questionnaire

This document specifies the questions that need to be answered by Subject Matter Experts (SMEs) to complete a California CPRA Risk Assessment. Each question indicates what Fides data can inform the answer and the level of automation possible.

**Coverage Legend:**
- **Full** - Fides can fully answer this question automatically
- **Partial** - Fides provides some data; SME review/supplementation needed
- **None** - Requires manual SME input; no Fides data available

---

## 1. Processing Scope and Purpose(s)

**Regulatory Requirement:** Describe the processing activity, its purpose(s), and why it is needed.

**Required:** Yes

### SME Questions

| # | Question | Coverage | Fides Data Sources |
|---|----------|----------|-------------------|
| 1.1 | What is the name and description of this processing activity? | **Partial** | `fides.system` (name, description), `fides.system.privacy_declarations` (declaration name) |
| 1.2 | What are the specific purposes for processing personal information? | **Partial** | `fides.system.privacy_declarations` (data_use), `fides.taxonomy.data_use` (purpose hierarchy) |
| 1.3 | Why is this processing necessary for the business? What business need does it address? | **None** | *Manual input required* |
| 1.4 | What is the scale of processing (number of consumers, volume of data, geographic scope)? | **None** | *Manual input required* - `external.scale_context` |
| 1.5 | How frequently does this processing occur? | **None** | *Manual input required* |

### Fides Data Available
```
From System:
- system.name, system.description
- system.system_type
- system.administrating_department

From Privacy Declarations:
- declaration.name (Processing Activity name)
- declaration.data_use (linked to taxonomy)

From Data Use Taxonomy:
- Hierarchical purposes (e.g., "marketing.advertising.first_party")
```

---

## 2. Significant Risk Determination

**Regulatory Requirement:** Determine whether the processing presents significant risk to consumers' privacy and document the basis for that determination.

**Required:** Yes

### SME Questions

| # | Question | Coverage | Fides Data Sources |
|---|----------|----------|-------------------|
| 2.1 | Does this processing involve selling personal information? | **Partial** | `fides.taxonomy.data_use` (third_party_sharing purposes), `fides.privacy_declaration.third_parties` |
| 2.2 | Does this processing involve sharing PI for cross-context behavioral advertising? | **Partial** | `fides.taxonomy.data_use`, `fides.asset` (ad pixels/trackers) |
| 2.3 | Does this processing involve sensitive personal information? | **Full** | `fides.privacy_declaration.special_categories`, `fides.taxonomy.data_category` |
| 2.4 | Does this processing involve automated decision-making technology (ADMT)? | **Partial** | `fides.system.legal_basis` (uses_profiling field) |
| 2.5 | What specific risks to consumers does this processing present? | **None** | *Manual input required* - `external.risk_register` |
| 2.6 | Why does this processing meet the threshold for "significant risk"? | **None** | *Manual input required* |

### Fides Data Available
```
From Privacy Declarations:
- processes_special_category_data (Boolean)
- data_shared_with_third_parties (Boolean)

From System:
- uses_profiling (Boolean)

From Data Use Taxonomy:
- third_party_sharing.*
- marketing.advertising.*
- personalize.*
```

---

## 3. Categories of Personal/Sensitive Personal Information

**Regulatory Requirement:** Identify the categories of personal information and sensitive personal information involved.

**Required:** Yes

### SME Questions

| # | Question | Coverage | Fides Data Sources |
|---|----------|----------|-------------------|
| 3.1 | What categories of personal information are collected and processed? | **Full** | `fides.dataset` (field-level data categories), `fides.taxonomy.data_category` |
| 3.2 | What categories of sensitive personal information (SPI) are involved? | **Full** | `fides.taxonomy.data_category` (sensitive categories), `fides.privacy_declaration.special_categories` |
| 3.3 | For each SPI category, what is the specific data collected? | **Full** | `fides.dataset` (field-level mapping), `fides.dataset_config` |
| 3.4 | Are there any data categories not yet mapped in your data inventory? | **Partial** | Compare `fides.dataset` against actual data sources |

### Fides Data Available
```
From Dataset:
- Field-level data_categories[] mapping
- Collection/table structure

From Data Category Taxonomy:
- Full hierarchy with sensitive categories flagged:
  - user.biometric
  - user.health
  - user.government_id
  - user.financial
  - user.genetic
  - user.geolocation.precise
  - user.race_ethnicity
  - user.religious_belief
  - user.sexual_orientation
  - user.credentials
```

---

## 4. Benefits vs. Risks Analysis

**Regulatory Requirement:** Weigh the benefits of the processing to the business, consumer, other stakeholders, and the public against the potential risks to consumers' privacy.

**Required:** Yes

### SME Questions

| # | Question | Coverage | Fides Data Sources |
|---|----------|----------|-------------------|
| 4.1 | What are the benefits of this processing to the business? | **None** | *Manual input required* |
| 4.2 | What are the benefits of this processing to consumers? | **None** | *Manual input required* |
| 4.3 | What are the benefits to other stakeholders or the public? | **None** | *Manual input required* |
| 4.4 | What are the potential privacy risks to consumers? | **None** | *Manual input required* - `external.risk_register` |
| 4.5 | How do the benefits outweigh the risks? | **None** | *Manual input required* |
| 4.6 | Could the same benefits be achieved with less invasive processing? | **None** | *Manual input required* |

### Fides Data Available
```
No direct Fides data for benefits/risks analysis.
This requires business context and legal/privacy team input.

Custom fields can be configured to capture:
- fides.custom_field (benefit_description, risk_score, etc.)
```

---

## 5. Risk Mitigation Measures

**Regulatory Requirement:** Document the safeguards and mitigation measures implemented to address identified risks.

**Required:** Yes

### SME Questions

| # | Question | Coverage | Fides Data Sources |
|---|----------|----------|-------------------|
| 5.1 | What technical safeguards protect the personal information? | **Partial** | `fides.system.security_practices`, `fides.policy` (masking strategies) |
| 5.2 | What organizational safeguards are in place (training, access controls, policies)? | **None** | *Manual input required* - `external.security_controls` |
| 5.3 | How are the identified risks mitigated by these safeguards? | **None** | *Manual input required* |
| 5.4 | What residual risks remain after mitigation? | **None** | *Manual input required* - `external.risk_register` |
| 5.5 | Is the residual risk acceptable? Who approved it? | **None** | *Manual input required* |

### Fides Data Available
```
From System:
- data_security_practices (free text field)

From Policy:
- Masking strategies (erasure, hash, null, etc.)
- Rules defining data protection by category
```

---

## 6. Automated Decision-Making Technology (ADMT)

**Regulatory Requirement:** If ADMT is used, document its use and safeguards.

**Required:** Yes (if applicable)

### SME Questions

| # | Question | Coverage | Fides Data Sources |
|---|----------|----------|-------------------|
| 6.1 | Does this processing use automated decision-making technology? | **Partial** | `fides.system.legal_basis` (uses_profiling), `fides.taxonomy.data_use` |
| 6.2 | What decisions are made or supported by ADMT? | **None** | *Manual input required* - `external.automated_decision_details` |
| 6.3 | How does the ADMT work (logic, algorithm, model)? | **None** | *Manual input required* |
| 6.4 | What inputs does the ADMT use? | **Partial** | `fides.dataset` (if ADMT system is mapped) |
| 6.5 | What safeguards exist for ADMT (human review, appeals, bias testing)? | **None** | *Manual input required* |
| 6.6 | How can consumers opt out of ADMT or request human review? | **Partial** | `fides.privacy_experience` (opt-out UI) |

### Fides Data Available
```
From System:
- uses_profiling (Boolean)
- legal_basis_for_profiling

From Data Subject:
- automated_decisions_or_profiling (per subject type)

From Data Use:
- personalize.*
- analytics.*
- improve.*
```

---

## 7. Review Cycle

**Regulatory Requirement:** Establish a review and update cadence for the risk assessment.

**Required:** Yes

### SME Questions

| # | Question | Coverage | Fides Data Sources |
|---|----------|----------|-------------------|
| 7.1 | How often will this risk assessment be reviewed? | **None** | *Manual input required* |
| 7.2 | What events would trigger an earlier review? | **Partial** | `fides.system_history` (change tracking) |
| 7.3 | Who is responsible for conducting reviews? | **None** | *Manual input required* |
| 7.4 | When was the last review conducted? | **Partial** | `fides.audit_log`, `fides.system.dpa_tracking` |
| 7.5 | What changes have been made since the last review? | **Partial** | `fides.system_history` (before/after snapshots) |

### Fides Data Available
```
From System History:
- before/after JSON snapshots
- edited_by, created_at timestamps

From System DPA Tracking:
- dpa_progress (status)
- dpa_location (reference)

From Audit Log:
- User actions on resources
- Timestamps for accountability
```

---

## 8. Consumer Notification and Transparency

**Regulatory Requirement:** Document how consumers are informed about the processing.

**Required:** Yes

### SME Questions

| # | Question | Coverage | Fides Data Sources |
|---|----------|----------|-------------------|
| 8.1 | Where is this processing disclosed in the privacy policy? | **Full** | `fides.privacy_notice` (notice text, data_uses) |
| 8.2 | Are just-in-time notices provided at collection points? | **Partial** | `fides.privacy_experience` (banner/modal config) |
| 8.3 | Do notices clearly explain the purposes of processing? | **Partial** | `fides.privacy_notice_by_data_use` (purpose mapping) |
| 8.4 | Are notices provided in languages appropriate for consumers? | **Partial** | `fides.privacy_notice` (translations[]) |
| 8.5 | How is the "Notice at Collection" requirement satisfied? | **Full** | `fides.privacy_notice`, `fides.privacy_experience` |

### Fides Data Available
```
From Privacy Notice:
- name, notice_key
- data_uses[] (purposes covered)
- translations[] (multilingual)
- consent_mechanism

From Privacy Experience:
- Jurisdiction-specific UI configuration
- Banner/modal content and behavior

From Privacy Notice by Data Use:
- Direct mapping of purposes to notices
```

---

## 9. Consumer Rights Mechanisms

**Regulatory Requirement:** Document mechanisms for consumers to exercise CCPA rights (know, access, delete, correct, opt-out, limit use of sensitive PI).

**Required:** Yes

### SME Questions

| # | Question | Coverage | Fides Data Sources |
|---|----------|----------|-------------------|
| 9.1 | How can consumers submit requests to know/access their data? | **Full** | `fides.taxonomy.data_subject.rights`, `fides.privacy_experience` |
| 9.2 | How can consumers request deletion of their data? | **Partial** | `fides.privacy_request` (deletion request handling) |
| 9.3 | How can consumers request correction of their data? | **Partial** | `fides.privacy_request` (correction handling) |
| 9.4 | How can consumers opt out of sale/sharing? | **Full** | `fides.privacy_experience` (opt-out UI) |
| 9.5 | How can consumers limit use of sensitive PI? | **Partial** | `fides.privacy_experience`, `fides.privacy_preferences` |
| 9.6 | What is the process for verifying consumer identity? | **None** | *Manual input required* |
| 9.7 | What is the timeline for responding to requests? | **None** | *Manual input required* |

### Fides Data Available
```
From Data Subject Rights:
- Rights configuration per subject type
- Supported request types

From Privacy Request:
- Request logs and status
- Processing evidence

From Privacy Experience:
- Rights submission UI/flows
- Opt-out mechanisms
```

---

## 10. Retention Periods

**Regulatory Requirement:** Specify retention periods for personal information used in this processing.

**Required:** Yes

### SME Questions

| # | Question | Coverage | Fides Data Sources |
|---|----------|----------|-------------------|
| 10.1 | How long is personal information retained for this processing? | **Partial** | `fides.privacy_declaration.retention` (retention_period field) |
| 10.2 | What is the legal/business basis for this retention period? | **None** | *Manual input required* - `external.retention_schedule` |
| 10.3 | How is data deleted or de-identified after the retention period? | **Partial** | `fides.policy` (masking strategies) |
| 10.4 | Are there different retention periods for different data categories? | **Partial** | `fides.privacy_declaration.retention` (per declaration) |

### Fides Data Available
```
From Privacy Declaration:
- retention_period (per processing activity)

From Policy:
- Masking/erasure strategies for deletion
```

---

## 11. Third-Party Recipients

**Regulatory Requirement:** Identify third parties receiving data, their purposes, and contractual safeguards.

**Required:** Yes

### SME Questions

| # | Question | Coverage | Fides Data Sources |
|---|----------|----------|-------------------|
| 11.1 | What third parties receive personal information from this processing? | **Partial** | `fides.connection_config`, `fides.privacy_declaration.third_parties`, `fides.system.data_flows` |
| 11.2 | What is the purpose of each third-party disclosure? | **Partial** | `fides.privacy_declaration.third_parties` (purpose in data_use) |
| 11.3 | What categories of PI are shared with each third party? | **Partial** | `fides.privacy_declaration.third_parties` (shared_categories) |
| 11.4 | How are third parties classified (service provider, contractor, third party)? | **Partial** | `fides.connection_config` (connection_type) |
| 11.5 | What contractual safeguards are in place? | **None** | *Manual input required* - `external.vendors_processors` |

### Fides Data Available
```
From Connection Config:
- Third-party connections (40+ types)
- Connection type classification
- System linkage

From Privacy Declaration:
- data_shared_with_third_parties (Boolean)
- third_parties (description)
- shared_categories[]

From Data Flows:
- Egress destinations
- Data categories flowing out
```

---

## 12. Service Provider/Contractor Contracts

**Regulatory Requirement:** Document service provider and contractor agreements with required CCPA provisions.

**Required:** Yes

### SME Questions

| # | Question | Coverage | Fides Data Sources |
|---|----------|----------|-------------------|
| 12.1 | Which third parties are classified as "service providers" vs "contractors"? | **Partial** | `fides.connection_config` |
| 12.2 | Do contracts include required CCPA provisions? | **None** | *Manual input required* - `external.vendors_processors` |
| 12.3 | Do contracts prohibit selling/sharing of received PI? | **None** | *Manual input required* |
| 12.4 | Do contracts require service providers to assist with consumer requests? | **None** | *Manual input required* |
| 12.5 | Are there subprocessor/subcontractor disclosures? | **None** | *Manual input required* |

### Fides Data Available
```
From Connection Config:
- Processor/vendor identification
- Connection types and system linkage

Contract details are not stored in Fides and require
external vendor management system or manual documentation.
```

---

## 13. Sensitive Personal Information Handling

**Regulatory Requirement:** If sensitive PI is processed, document specific safeguards and consumer right to limit use.

**Required:** Yes

### SME Questions

| # | Question | Coverage | Fides Data Sources |
|---|----------|----------|-------------------|
| 13.1 | What categories of sensitive PI are processed? | **Full** | `fides.taxonomy.data_category`, `fides.privacy_declaration.special_categories` |
| 13.2 | Is consent obtained for sensitive PI processing? | **Partial** | `fides.privacy_declaration.legal_basis` (special_category_legal_basis) |
| 13.3 | Can consumers limit use of their sensitive PI? | **Partial** | `fides.privacy_experience` (limit use UI) |
| 13.4 | What additional safeguards protect sensitive PI? | **Partial** | `fides.system.security_practices`, `fides.policy` |
| 13.5 | Is sensitive PI used only for permitted purposes (essential services)? | **Partial** | `fides.taxonomy.data_use` (purpose classification) |

### Fides Data Available
```
From Privacy Declaration:
- processes_special_category_data (Boolean)
- special_category_legal_basis

From Data Category Taxonomy:
- Sensitive category identification
- Hierarchical classification

From Privacy Experience:
- "Limit Use of Sensitive PI" toggle/mechanism
```

---

## 14. Technical and Organizational Safeguards

**Regulatory Requirement:** Document security measures protecting PI during this processing.

**Required:** Yes

### SME Questions

| # | Question | Coverage | Fides Data Sources |
|---|----------|----------|-------------------|
| 14.1 | What technical measures protect data at rest? | **Partial** | `fides.system.security_practices` |
| 14.2 | What technical measures protect data in transit? | **None** | *Manual input required* - `external.security_controls` |
| 14.3 | What access controls limit who can access PI? | **Partial** | `fides.policy` (access rules) |
| 14.4 | How is data minimized or pseudonymized? | **Partial** | `fides.policy` (masking strategies) |
| 14.5 | What organizational measures support security (training, policies)? | **None** | *Manual input required* |
| 14.6 | What incident response procedures exist? | **None** | *Manual input required* |

### Fides Data Available
```
From System:
- data_security_practices (free text)

From Policy:
- Masking strategies (erasure, hash, null, random_string, etc.)
- Access/erasure rules by data category
```

---

## 15. Consumer Harm Categories

**Regulatory Requirement:** Identify and evaluate specific harm types (discrimination, financial, physical, reputational, intrusion).

**Required:** Yes

### SME Questions

| # | Question | Coverage | Fides Data Sources |
|---|----------|----------|-------------------|
| 15.1 | Could this processing result in unlawful discrimination? | **None** | *Manual input required* - `external.risk_register` |
| 15.2 | Could this processing cause financial harm to consumers? | **None** | *Manual input required* |
| 15.3 | Could this processing cause physical harm? | **None** | *Manual input required* |
| 15.4 | Could this processing cause reputational harm? | **None** | *Manual input required* |
| 15.5 | Does this processing constitute an unreasonable intrusion into privacy? | **None** | *Manual input required* |
| 15.6 | What is the likelihood and severity of each harm type? | **None** | *Manual input required* |

### Fides Data Available
```
No direct Fides data for harm assessment.
Custom fields can be configured to capture harm scoring:
- fides.custom_field (harm_type, likelihood, severity, etc.)

This analysis requires legal/privacy team expertise.
```

---

## 16. Selling and Sharing of PI

**Regulatory Requirement:** If selling or sharing for cross-context behavioral advertising, document safeguards and opt-out mechanisms.

**Required:** Yes

### SME Questions

| # | Question | Coverage | Fides Data Sources |
|---|----------|----------|-------------------|
| 16.1 | Does this processing involve "selling" PI as defined by CCPA? | **Full** | `fides.taxonomy.data_use` (third_party_sharing purposes) |
| 16.2 | Does this processing involve "sharing" for cross-context behavioral advertising? | **Full** | `fides.taxonomy.data_use`, `fides.asset` (ad trackers) |
| 16.3 | What PI is sold or shared? | **Partial** | `fides.privacy_declaration.third_parties` (shared_categories) |
| 16.4 | To whom is PI sold or shared? | **Partial** | `fides.connection_config`, `fides.privacy_declaration.third_parties` |
| 16.5 | How can consumers opt out of sale/sharing? | **Full** | `fides.privacy_experience` (opt-out UI), `fides.privacy_notice` |
| 16.6 | Is the "Do Not Sell or Share" link prominently displayed? | **Partial** | `fides.privacy_experience` |

### Fides Data Available
```
From Data Use Taxonomy:
- third_party_sharing.*
- marketing.advertising.*
- marketing.advertising.third_party

From Privacy Declaration:
- data_shared_with_third_parties (Boolean)
- third_parties (description)
- shared_categories[]

From Privacy Notice:
- Sale/sharing disclosures
- Opt-out information

From Privacy Experience:
- "Do Not Sell or Share" UI component
```

---

## 17. Opt-Out Mechanisms

**Regulatory Requirement:** Document opt-out mechanisms including Do Not Sell/Share links and universal opt-out signal recognition.

**Required:** Yes

### SME Questions

| # | Question | Coverage | Fides Data Sources |
|---|----------|----------|-------------------|
| 17.1 | Is a "Do Not Sell or Share My Personal Information" link provided? | **Full** | `fides.privacy_experience` |
| 17.2 | Does the business recognize Global Privacy Control (GPC) signals? | **Full** | `fides.privacy_experience` (has_gpc_flag), `fides.config` |
| 17.3 | How are opt-out preferences honored across systems? | **Partial** | `fides.privacy_preferences`, `fides.consent_request` |
| 17.4 | Are opt-out preferences persisted and respected? | **Partial** | `fides.privacy_preferences` |
| 17.5 | How is opt-out communicated to third parties? | **Partial** | `fides.consent_request` (fulfillment status) |

### Fides Data Available
```
From Privacy Experience:
- Opt-out UI configuration
- GPC signal handling
- Jurisdiction-specific flows

From Privacy Preferences:
- Stored consent/opt-out choices
- Per-identity/device preferences

From Config:
- GPC/UOO settings enabled
- Consent behavior configuration

From Consent Request:
- Opt-out propagation to downstream systems
- Fulfillment status
```

---

## 18. Executive Certification

**Regulatory Requirement:** Obtain sign-off from responsible executive on assessment completeness and accuracy.

**Required:** Yes

### SME Questions

| # | Question | Coverage | Fides Data Sources |
|---|----------|----------|-------------------|
| 18.1 | Who is the responsible executive for this assessment? | **None** | *Manual input required* |
| 18.2 | Has the executive reviewed and approved this assessment? | **None** | *Manual input required* |
| 18.3 | What is the date of executive certification? | **Partial** | `fides.custom_field` (can track sign-off date) |
| 18.4 | Is there documentation of the executive's review? | **None** | *Manual input required* |

### Fides Data Available
```
No direct executive sign-off tracking in Fides.
Custom fields can be configured:
- fides.custom_field (certifying_executive, certification_date, etc.)
- fides.audit_log (tracks user actions for accountability)
```

---

## 19. Children's Data Considerations (Optional)

**Regulatory Requirement:** If processing data of consumers under 16, document additional protections and opt-in consent requirements.

**Required:** No (only if processing children's data)

### SME Questions

| # | Question | Coverage | Fides Data Sources |
|---|----------|----------|-------------------|
| 19.1 | Does this processing involve data of consumers under 16? | **Partial** | `fides.taxonomy.data_subject` (can include "child" subject) |
| 19.2 | Is opt-in consent obtained for consumers 13-15? | **None** | *Manual input required* - `external.children_context` |
| 19.3 | Is verifiable parental consent obtained for consumers under 13? | **None** | *Manual input required* |
| 19.4 | What age verification methods are used? | **None** | *Manual input required* |
| 19.5 | What additional protections exist for children's data? | **None** | *Manual input required* |

### Fides Data Available
```
From Data Subject Taxonomy:
- Can define "child" or "minor" subject types

Children-specific handling is largely manual:
- external.children_context for age-gating and safeguards
```

---

## 20. Prior Assessment References (Optional)

**Regulatory Requirement:** Reference any prior risk assessments for related processing activities.

**Required:** No

### SME Questions

| # | Question | Coverage | Fides Data Sources |
|---|----------|----------|-------------------|
| 20.1 | Have prior risk assessments been conducted for this or similar processing? | **Partial** | `fides.system.dpa_tracking` (dpa_location, dpa_progress) |
| 20.2 | What were the findings of prior assessments? | **Partial** | `fides.system_history` (historical snapshots) |
| 20.3 | How does this assessment build on prior work? | **None** | *Manual input required* |

### Fides Data Available
```
From System DPA Tracking:
- requires_data_protection_assessments (Boolean)
- dpa_location (reference/URL)
- dpa_progress (status)

From System History:
- Historical before/after snapshots
- Change tracking over time
```

---

## Summary: Coverage by Requirement

| Requirement | Coverage | Full Auto Questions | Partial Questions | Manual Questions |
|-------------|----------|---------------------|-------------------|------------------|
| Processing Scope | Partial | 0 | 2 | 3 |
| Significant Risk | Partial | 1 | 3 | 2 |
| Data Categories | **Full** | 3 | 1 | 0 |
| Benefits vs Risks | None | 0 | 0 | 6 |
| Mitigation | Partial | 0 | 1 | 4 |
| ADMT | Partial | 0 | 3 | 3 |
| Review Cycle | Partial | 0 | 3 | 2 |
| Consumer Notification | **Full** | 2 | 3 | 0 |
| Consumer Rights | Partial | 2 | 3 | 2 |
| Retention Periods | Partial | 0 | 3 | 1 |
| Third-Party Recipients | Partial | 0 | 4 | 1 |
| Service Provider Contracts | Partial | 0 | 1 | 4 |
| Sensitive PI | **Full** | 1 | 4 | 0 |
| Technical Safeguards | Partial | 0 | 3 | 3 |
| Consumer Harm | None | 0 | 0 | 6 |
| Selling/Sharing | **Full** | 3 | 3 | 0 |
| Opt-Out Mechanisms | **Full** | 2 | 3 | 0 |
| Executive Certification | None | 0 | 1 | 3 |
| Children's Data | Partial | 0 | 1 | 4 |
| Prior Assessments | Partial | 0 | 2 | 1 |

**Overall:** ~80% of requirements can be partially or fully informed by Fides data. ~20% require purely manual SME input.
