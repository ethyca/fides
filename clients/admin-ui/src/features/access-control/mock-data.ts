import {
  DailyViolationData,
  DataConsumer,
  HourlyViolationData,
  MonthlyViolationData,
  RequestLogEntry,
  ViolationSummary,
} from "./types";

export const MOCK_MONTHLY_VIOLATIONS: MonthlyViolationData[] = [
  { month: "Jan", violations: 3 },
  { month: "Feb", violations: 2 },
  { month: "Mar", violations: 5 },
  { month: "Apr", violations: 4 },
  { month: "May", violations: 6 },
  { month: "Jun", violations: 8 },
  { month: "Jul", violations: 12 },
  { month: "Aug", violations: 10 },
  { month: "Sep", violations: 15 },
  { month: "Oct", violations: 18 },
  { month: "Nov", violations: 22 },
  { month: "Dec", violations: 27 },
];

export const MOCK_SPARKLINE_DATA: number[] = MOCK_MONTHLY_VIOLATIONS.map(
  (d) => d.violations,
);

export const MOCK_VIOLATION_RATE = 5.4;
export const MOCK_TOTAL_VIOLATIONS = 95;
export const MOCK_TOTAL_REQUESTS = 1760;

export const MOCK_DATA_CONSUMERS: DataConsumer[] = [
  { name: "Jack Gale", requests: 312, violations: 12 },
  { name: "Sarah Chen", requests: 188, violations: 15 },
  { name: "Alex Rivera", requests: 94, violations: 0 },
  { name: "Priya Patel", requests: 156, violations: 8 },
];

export const MOCK_FINDINGS: ViolationSummary[] = [
  {
    id: "finding_1",
    policyName: "HIPAA_COMPLIANCE",
    controlName: "SENSITIVE_DATA_RESTRICTION",
    violationCount: 15,
    lastViolation: "2026-02-18T14:22:01Z",
  },
  {
    id: "finding_2",
    policyName: "PII_SECURITY",
    controlName: "PII_ACCESS_CONTROL",
    violationCount: 12,
    lastViolation: "2026-03-10T13:45:12Z",
  },
  {
    id: "finding_3",
    policyName: "CCPA_RESTRICT",
    controlName: "CROSS_BORDER_DATA_FLOW",
    violationCount: 10,
    lastViolation: "2026-03-01T11:10:05Z",
  },
  {
    id: "finding_4",
    policyName: "GDPR_CONSENT",
    controlName: "CONSENT_VERIFICATION",
    violationCount: 9,
    lastViolation: "2026-03-11T12:05:18Z",
  },
  {
    id: "finding_5",
    policyName: "PII_SHIELD",
    controlName: "CUSTOMER_DATA_MASKING",
    violationCount: 8,
    lastViolation: "2026-01-30T09:30:00Z",
  },
  {
    id: "finding_6",
    policyName: "HIPAA_COMPLIANCE",
    controlName: "PHI_ENCRYPTION_CHECK",
    violationCount: 7,
    lastViolation: "2026-03-09T18:45:22Z",
  },
  {
    id: "finding_7",
    policyName: "PII_SECURITY",
    controlName: "COLUMN_MASKING_BYPASS",
    violationCount: 6,
    lastViolation: "2026-02-11T10:44:30Z",
  },
  {
    id: "finding_8",
    policyName: "CCPA_RESTRICT",
    controlName: "OPT_OUT_ENFORCEMENT",
    violationCount: 5,
    lastViolation: "2026-03-06T21:30:15Z",
  },
  {
    id: "finding_9",
    policyName: "GDPR_CONSENT",
    controlName: "PREFERENCE_EXPIRY_CHECK",
    violationCount: 5,
    lastViolation: "2026-02-04T16:12:44Z",
  },
  {
    id: "finding_10",
    policyName: "PII_SHIELD",
    controlName: "DATA_EXPORT_MASKING",
    violationCount: 4,
    lastViolation: "2026-03-08T07:50:33Z",
  },
  {
    id: "finding_11",
    policyName: "HIPAA_COMPLIANCE",
    controlName: "AUDIT_TRAIL_INTEGRITY",
    violationCount: 4,
    lastViolation: "2026-02-25T15:05:28Z",
  },
  {
    id: "finding_12",
    policyName: "PII_SECURITY",
    controlName: "TOKEN_REUSE_DETECTION",
    violationCount: 3,
    lastViolation: "2026-03-04T06:30:12Z",
  },
  {
    id: "finding_13",
    policyName: "CCPA_RESTRICT",
    controlName: "CONSENT_SCOPE_MISMATCH",
    violationCount: 3,
    lastViolation: "2026-01-28T11:22:45Z",
  },
  {
    id: "finding_14",
    policyName: "GDPR_CONSENT",
    controlName: "RETENTION_PERIOD_EXCEEDED",
    violationCount: 2,
    lastViolation: "2026-03-02T14:30:00Z",
  },
  {
    id: "finding_15",
    policyName: "PII_SHIELD",
    controlName: "UNMASKED_FIELD_ACCESS",
    violationCount: 2,
    lastViolation: "2026-02-14T09:10:00Z",
  },
];

export const MOCK_DAILY_VIOLATIONS: DailyViolationData[] = [
  { day: "Feb 11", violations: 8 },
  { day: "Feb 12", violations: 7 },
  { day: "Feb 13", violations: 9 },
  { day: "Feb 14", violations: 8 },
  { day: "Feb 15", violations: 7 },
  { day: "Feb 16", violations: 8 },
  { day: "Feb 17", violations: 6 },
  { day: "Feb 18", violations: 7 },
  { day: "Feb 19", violations: 5 },
  { day: "Feb 20", violations: 6 },
  { day: "Feb 21", violations: 7 },
  { day: "Feb 22", violations: 5 },
  { day: "Feb 23", violations: 6 },
  { day: "Feb 24", violations: 5 },
  { day: "Feb 25", violations: 4 },
  { day: "Feb 26", violations: 5 },
  { day: "Feb 27", violations: 6 },
  { day: "Feb 28", violations: 4 },
  { day: "Mar 1", violations: 5 },
  { day: "Mar 2", violations: 4 },
  { day: "Mar 3", violations: 3 },
  { day: "Mar 4", violations: 4 },
  { day: "Mar 5", violations: 3 },
  { day: "Mar 6", violations: 4 },
  { day: "Mar 7", violations: 3 },
  { day: "Mar 8", violations: 2 },
  { day: "Mar 9", violations: 3 },
  { day: "Mar 10", violations: 2 },
  { day: "Mar 11", violations: 2 },
  { day: "Mar 12", violations: 3 },
];

// 6-hour buckets over 30 days (120 data points) for dense bar chart
export const MOCK_HOURLY_VIOLATIONS: HourlyViolationData[] = [
  { label: "Feb 11", violations: 1 },
  { label: "", violations: 3 },
  { label: "", violations: 0 },
  { label: "", violations: 2 },
  { label: "Feb 12", violations: 4 },
  { label: "", violations: 1 },
  { label: "", violations: 5 },
  { label: "", violations: 2 },
  { label: "Feb 13", violations: 0 },
  { label: "", violations: 2 },
  { label: "", violations: 1 },
  { label: "", violations: 0 },
  { label: "Feb 14", violations: 3 },
  { label: "", violations: 1 },
  { label: "", violations: 2 },
  { label: "", violations: 0 },
  { label: "Feb 15", violations: 0 },
  { label: "", violations: 0 },
  { label: "", violations: 1 },
  { label: "", violations: 0 },
  { label: "Feb 16", violations: 2 },
  { label: "", violations: 1 },
  { label: "", violations: 3 },
  { label: "", violations: 0 },
  { label: "Feb 17", violations: 4 },
  { label: "", violations: 2 },
  { label: "", violations: 3 },
  { label: "", violations: 1 },
  { label: "Feb 18", violations: 5 },
  { label: "", violations: 3 },
  { label: "", violations: 6 },
  { label: "", violations: 2 },
  { label: "Feb 19", violations: 1 },
  { label: "", violations: 4 },
  { label: "", violations: 2 },
  { label: "", violations: 0 },
  { label: "Feb 20", violations: 3 },
  { label: "", violations: 5 },
  { label: "", violations: 2 },
  { label: "", violations: 1 },
  { label: "Feb 21", violations: 0 },
  { label: "", violations: 2 },
  { label: "", violations: 1 },
  { label: "", violations: 0 },
  { label: "Feb 22", violations: 4 },
  { label: "", violations: 6 },
  { label: "", violations: 3 },
  { label: "", violations: 1 },
  { label: "Feb 23", violations: 7 },
  { label: "", violations: 5 },
  { label: "", violations: 4 },
  { label: "", violations: 2 },
  { label: "Feb 24", violations: 2 },
  { label: "", violations: 3 },
  { label: "", violations: 1 },
  { label: "", violations: 4 },
  { label: "Feb 25", violations: 1 },
  { label: "", violations: 0 },
  { label: "", violations: 3 },
  { label: "", violations: 2 },
  { label: "Feb 26", violations: 5 },
  { label: "", violations: 3 },
  { label: "", violations: 4 },
  { label: "", violations: 1 },
  { label: "Feb 27", violations: 2 },
  { label: "", violations: 4 },
  { label: "", violations: 1 },
  { label: "", violations: 0 },
  { label: "Feb 28", violations: 6 },
  { label: "", violations: 4 },
  { label: "", violations: 5 },
  { label: "", violations: 3 },
  { label: "Mar 1", violations: 3 },
  { label: "", violations: 2 },
  { label: "", violations: 4 },
  { label: "", violations: 1 },
  { label: "Mar 2", violations: 1 },
  { label: "", violations: 3 },
  { label: "", violations: 2 },
  { label: "", violations: 0 },
  { label: "Mar 3", violations: 6 },
  { label: "", violations: 4 },
  { label: "", violations: 5 },
  { label: "", violations: 3 },
  { label: "Mar 4", violations: 2 },
  { label: "", violations: 5 },
  { label: "", violations: 3 },
  { label: "", violations: 1 },
  { label: "Mar 5", violations: 8 },
  { label: "", violations: 6 },
  { label: "", violations: 5 },
  { label: "", violations: 3 },
  { label: "Mar 6", violations: 4 },
  { label: "", violations: 3 },
  { label: "", violations: 5 },
  { label: "", violations: 2 },
  { label: "Mar 7", violations: 1 },
  { label: "", violations: 4 },
  { label: "", violations: 3 },
  { label: "", violations: 0 },
  { label: "Mar 8", violations: 7 },
  { label: "", violations: 5 },
  { label: "", violations: 6 },
  { label: "", violations: 3 },
  { label: "Mar 9", violations: 1 },
  { label: "", violations: 2 },
  { label: "", violations: 0 },
  { label: "", violations: 3 },
  { label: "Mar 10", violations: 5 },
  { label: "", violations: 4 },
  { label: "", violations: 3 },
  { label: "", violations: 2 },
  { label: "Mar 11", violations: 3 },
  { label: "", violations: 2 },
  { label: "", violations: 4 },
  { label: "", violations: 1 },
  { label: "Mar 12", violations: 4 },
  { label: "", violations: 5 },
  { label: "", violations: 3 },
  { label: "", violations: 2 },
];

export const MOCK_TOTAL_REQUEST_LOG_VIOLATIONS = 214;

export const MOCK_REQUEST_LOG: RequestLogEntry[] = [
  {
    id: "req_1",
    timestamp: "2023-11-24T14:22:01Z",
    consumer: "Jack Gale",
    consumerEmail: "jack@fides.ai",
    policy: "HIPAA_COMPLIANCE",
    controlName: "SENSITIVE_DATA_RESTRICTION",
    policyDescription:
      "Restrict all Billing_Data access unless requester has Security_Level_3 and matches Financial_Audit intent header.",
    dataset: "production.billing",
    table: "credit_cards",
    dataUse: "Marketing",
    system: "Snowflake",
    violationReason:
      "This request attempted to access raw HIPAA-protected billing identifiers from a production marketing endpoint without the required Encryption_At_Rest and Strict_PII scopes enabled.",
    requestContext:
      "SELECT * FROM customer_v2.credit_cards\nWHERE region = 'EMEA'\nAND card_type = 'PLATINUM'\nLIMIT 1000;",
  },
  {
    id: "req_2",
    timestamp: "2023-11-24T14:21:30Z",
    consumer: "Marketing-Service",
    consumerEmail: "service@internal",
    policy: "PII_SECURITY",
    controlName: "PII_ACCESS_CONTROL",
    policyDescription:
      "Prevent any service account from accessing PII columns without explicit data use declaration.",
    dataset: "analytics.users",
    table: "user_profiles",
    dataUse: "Identity",
    system: "BigQuery",
    violationReason:
      "Service account Marketing-Service accessed PII columns in analytics.users without a declared identity data use purpose.",
    requestContext:
      "SELECT email, phone, full_name\nFROM analytics.users.user_profiles\nWHERE signup_date > '2023-01-01';",
  },
  {
    id: "req_3",
    timestamp: "2023-11-24T14:19:12Z",
    consumer: "Production-App-SA",
    consumerEmail: "prod-sa@internal",
    policy: "CCPA_RESTRICT",
    controlName: "CROSS_BORDER_DATA_FLOW",
    policyDescription:
      "Block cross-border data transfers for California residents unless explicit consent is recorded.",
    dataset: "external.leads",
    table: "lead_contacts",
    dataUse: "Sales",
    system: "PostgreSQL",
    violationReason:
      "Production service account attempted to export California resident lead data to an external endpoint without matching consent records.",
    requestContext:
      "SELECT * FROM external.leads.lead_contacts\nWHERE state = 'CA'\nAND export_flag = true;",
  },
  {
    id: "req_4",
    timestamp: "2023-11-24T14:15:45Z",
    consumer: "Sarah Chen",
    consumerEmail: "sarah@fides.ai",
    policy: "PII_SHIELD",
    controlName: "CUSTOMER_DATA_MASKING",
    policyDescription:
      "Require data masking for all customer profile queries outside of the production support context.",
    dataset: "customer.profiles",
    table: "customer_details",
    dataUse: "Identity",
    system: "Snowflake",
    violationReason:
      "User Sarah Chen queried unmasked customer profile data outside of the production support context.",
    requestContext:
      "SELECT ssn, date_of_birth, address\nFROM customer.profiles.customer_details\nWHERE customer_id IN (1042, 1055, 1089);",
  },
  {
    id: "req_5",
    timestamp: "2023-11-24T14:12:10Z",
    consumer: "Marketing-Service",
    consumerEmail: "service@internal",
    policy: "GDPR_CONSENT",
    controlName: "CONSENT_VERIFICATION",
    policyDescription:
      "Verify active consent records before allowing marketing data access for EU residents.",
    dataset: "marketing.leads",
    table: "email_campaigns",
    dataUse: "Marketing",
    system: "Redshift",
    violationReason:
      "Service account Marketing-Service accessed EU resident marketing data without verified consent records in the consent management platform.",
    requestContext:
      "SELECT email, campaign_id, engagement_score\nFROM marketing.leads.email_campaigns\nWHERE region = 'EU'\nAND opted_in IS NULL;",
  },
  {
    id: "req_6",
    timestamp: "2023-11-24T13:58:44Z",
    consumer: "Alex Rivera",
    consumerEmail: "alex@fides.ai",
    policy: "HIPAA_COMPLIANCE",
    controlName: "SENSITIVE_DATA_RESTRICTION",
    policyDescription:
      "Restrict all Billing_Data access unless requester has Security_Level_3 and matches Financial_Audit intent header.",
    dataset: "production.billing",
    table: "invoices",
    dataUse: "Identity",
    system: "Snowflake",
    violationReason:
      "User Alex Rivera queried billing invoice records containing patient identifiers without required HIPAA security level clearance.",
    requestContext:
      "SELECT invoice_id, patient_name, amount\nFROM production.billing.invoices\nWHERE created_at > '2023-10-01';",
  },
  {
    id: "req_7",
    timestamp: "2023-11-24T13:45:22Z",
    consumer: "ETL-Pipeline-SA",
    consumerEmail: "etl@internal",
    policy: "PII_SECURITY",
    controlName: "PII_ACCESS_CONTROL",
    policyDescription:
      "Prevent any service account from accessing PII columns without explicit data use declaration.",
    dataset: "warehouse.customers",
    table: "contact_info",
    dataUse: "Marketing",
    system: "BigQuery",
    violationReason:
      "ETL pipeline service account ingested raw PII contact columns without a declared marketing consent data use purpose.",
    requestContext:
      "INSERT INTO staging.contacts\nSELECT email, phone, address\nFROM warehouse.customers.contact_info;",
  },
  {
    id: "req_8",
    timestamp: "2023-11-24T13:30:15Z",
    consumer: "Jack Gale",
    consumerEmail: "jack@fides.ai",
    policy: "CCPA_RESTRICT",
    controlName: "CROSS_BORDER_DATA_FLOW",
    policyDescription:
      "Block cross-border data transfers for California residents unless explicit consent is recorded.",
    dataset: "analytics.geo",
    table: "user_locations",
    dataUse: "Sales",
    system: "PostgreSQL",
    violationReason:
      "User Jack Gale exported California resident location data to an analytics endpoint without matching CCPA consent records.",
    requestContext:
      "SELECT user_id, city, zip_code\nFROM analytics.geo.user_locations\nWHERE state = 'CA';",
  },
  {
    id: "req_9",
    timestamp: "2023-11-24T13:18:00Z",
    consumer: "Reporting-Service",
    consumerEmail: "reporting@internal",
    policy: "PII_SHIELD",
    controlName: "CUSTOMER_DATA_MASKING",
    policyDescription:
      "Require data masking for all customer profile queries outside of the production support context.",
    dataset: "customer.profiles",
    table: "demographics",
    dataUse: "Marketing",
    system: "Snowflake",
    violationReason:
      "Reporting service accessed unmasked demographic data outside of the production support context for dashboard generation.",
    requestContext:
      "SELECT age_range, income_bracket, zip_code\nFROM customer.profiles.demographics\nGROUP BY age_range, income_bracket;",
  },
  {
    id: "req_10",
    timestamp: "2023-11-24T12:55:33Z",
    consumer: "Sarah Chen",
    consumerEmail: "sarah@fides.ai",
    policy: "GDPR_CONSENT",
    controlName: "CONSENT_VERIFICATION",
    policyDescription:
      "Verify active consent records before allowing marketing data access for EU residents.",
    dataset: "marketing.leads",
    table: "newsletter_subscribers",
    dataUse: "Marketing",
    system: "Redshift",
    violationReason:
      "User Sarah Chen accessed EU newsletter subscriber list without verified GDPR consent records on file.",
    requestContext:
      "SELECT email, first_name, subscription_date\nFROM marketing.leads.newsletter_subscribers\nWHERE country IN ('DE', 'FR', 'IT');",
  },
  {
    id: "req_11",
    timestamp: "2023-11-24T12:40:18Z",
    consumer: "Data-Science-SA",
    consumerEmail: "ds@internal",
    policy: "HIPAA_COMPLIANCE",
    controlName: "SENSITIVE_DATA_RESTRICTION",
    policyDescription:
      "Restrict all Billing_Data access unless requester has Security_Level_3 and matches Financial_Audit intent header.",
    dataset: "production.billing",
    table: "payment_methods",
    dataUse: "Identity",
    system: "Snowflake",
    violationReason:
      "Data science service account accessed raw payment method records for model training without required security clearance.",
    requestContext:
      "SELECT card_last_four, expiry_date, billing_zip\nFROM production.billing.payment_methods\nLIMIT 50000;",
  },
  {
    id: "req_12",
    timestamp: "2023-11-24T12:22:05Z",
    consumer: "Alex Rivera",
    consumerEmail: "alex@fides.ai",
    policy: "PII_SECURITY",
    controlName: "PII_ACCESS_CONTROL",
    policyDescription:
      "Prevent any service account from accessing PII columns without explicit data use declaration.",
    dataset: "analytics.users",
    table: "login_history",
    dataUse: "Identity",
    system: "BigQuery",
    violationReason:
      "User Alex Rivera accessed login history containing IP addresses and device fingerprints without a declared identity data use.",
    requestContext:
      "SELECT user_id, ip_address, device_id, login_time\nFROM analytics.users.login_history\nWHERE login_time > NOW() - INTERVAL '7 days';",
  },
  {
    id: "req_13",
    timestamp: "2023-11-24T12:05:50Z",
    consumer: "Marketing-Service",
    consumerEmail: "service@internal",
    policy: "CCPA_RESTRICT",
    controlName: "CROSS_BORDER_DATA_FLOW",
    policyDescription:
      "Block cross-border data transfers for California residents unless explicit consent is recorded.",
    dataset: "external.leads",
    table: "prospect_list",
    dataUse: "Sales",
    system: "PostgreSQL",
    violationReason:
      "Marketing service exported California prospect data to a third-party enrichment API without consent verification.",
    requestContext:
      "SELECT prospect_id, email, company\nFROM external.leads.prospect_list\nWHERE state = 'CA'\nAND enrichment_pending = true;",
  },
  {
    id: "req_14",
    timestamp: "2023-11-24T11:48:30Z",
    consumer: "Jack Gale",
    consumerEmail: "jack@fides.ai",
    policy: "PII_SHIELD",
    controlName: "CUSTOMER_DATA_MASKING",
    policyDescription:
      "Require data masking for all customer profile queries outside of the production support context.",
    dataset: "customer.profiles",
    table: "financial_summary",
    dataUse: "Identity",
    system: "Snowflake",
    violationReason:
      "User Jack Gale accessed unmasked financial summary data including account balances outside of a support ticket context.",
    requestContext:
      "SELECT customer_id, account_balance, credit_score\nFROM customer.profiles.financial_summary\nWHERE credit_score < 600;",
  },
  {
    id: "req_15",
    timestamp: "2023-11-24T11:30:12Z",
    consumer: "Compliance-Bot",
    consumerEmail: "compliance@internal",
    policy: "GDPR_CONSENT",
    controlName: "CONSENT_VERIFICATION",
    policyDescription:
      "Verify active consent records before allowing marketing data access for EU residents.",
    dataset: "marketing.leads",
    table: "ad_targeting",
    dataUse: "Marketing",
    system: "Redshift",
    violationReason:
      "Compliance bot flagged ad targeting query against EU user segments where consent records had expired beyond the 12-month renewal window.",
    requestContext:
      "SELECT user_segment, interest_tags, last_seen\nFROM marketing.leads.ad_targeting\nWHERE region = 'EU'\nAND last_consent_date < '2022-11-01';",
  },
  {
    id: "req_16",
    timestamp: "2023-11-24T11:15:00Z",
    consumer: "Sarah Chen",
    consumerEmail: "sarah@fides.ai",
    policy: "HIPAA_COMPLIANCE",
    controlName: "SENSITIVE_DATA_RESTRICTION",
    policyDescription:
      "Restrict all Billing_Data access unless requester has Security_Level_3 and matches Financial_Audit intent header.",
    dataset: "production.billing",
    table: "claims",
    dataUse: "Identity",
    system: "Snowflake",
    violationReason:
      "User Sarah Chen accessed insurance claims records containing diagnosis codes without the required HIPAA security level.",
    requestContext:
      "SELECT claim_id, diagnosis_code, provider_name\nFROM production.billing.claims\nWHERE status = 'pending';",
  },
  {
    id: "req_17",
    timestamp: "2023-11-24T10:58:45Z",
    consumer: "ETL-Pipeline-SA",
    consumerEmail: "etl@internal",
    policy: "PII_SECURITY",
    controlName: "PII_ACCESS_CONTROL",
    policyDescription:
      "Prevent any service account from accessing PII columns without explicit data use declaration.",
    dataset: "warehouse.customers",
    table: "identity_documents",
    dataUse: "Identity",
    system: "BigQuery",
    violationReason:
      "ETL pipeline accessed identity document references including passport and SSN columns without explicit data use declaration.",
    requestContext:
      "SELECT customer_id, ssn_hash, passport_country\nFROM warehouse.customers.identity_documents\nWHERE verified = false;",
  },
  {
    id: "req_18",
    timestamp: "2023-11-24T10:40:22Z",
    consumer: "Production-App-SA",
    consumerEmail: "prod-sa@internal",
    policy: "CCPA_RESTRICT",
    controlName: "CROSS_BORDER_DATA_FLOW",
    policyDescription:
      "Block cross-border data transfers for California residents unless explicit consent is recorded.",
    dataset: "external.leads",
    table: "partner_sync",
    dataUse: "Sales",
    system: "PostgreSQL",
    violationReason:
      "Production service account synced California user records to a partner system located outside the US without explicit data sharing consent.",
    requestContext:
      "INSERT INTO partner_api.sync_queue\nSELECT user_id, email, purchase_history\nFROM external.leads.partner_sync\nWHERE state = 'CA';",
  },
  {
    id: "req_19",
    timestamp: "2023-11-24T10:22:10Z",
    consumer: "Alex Rivera",
    consumerEmail: "alex@fides.ai",
    policy: "PII_SHIELD",
    controlName: "CUSTOMER_DATA_MASKING",
    policyDescription:
      "Require data masking for all customer profile queries outside of the production support context.",
    dataset: "customer.profiles",
    table: "preferences",
    dataUse: "Marketing",
    system: "Snowflake",
    violationReason:
      "User Alex Rivera accessed customer preference data including sensitive health-related preferences without masking applied.",
    requestContext:
      "SELECT customer_id, dietary_preferences, allergy_info\nFROM customer.profiles.preferences\nWHERE updated_at > '2023-09-01';",
  },
  {
    id: "req_20",
    timestamp: "2023-11-24T10:05:55Z",
    consumer: "Reporting-Service",
    consumerEmail: "reporting@internal",
    policy: "GDPR_CONSENT",
    controlName: "CONSENT_VERIFICATION",
    policyDescription:
      "Verify active consent records before allowing marketing data access for EU residents.",
    dataset: "marketing.leads",
    table: "engagement_metrics",
    dataUse: "Marketing",
    system: "Redshift",
    violationReason:
      "Reporting service generated engagement metrics report using EU user data where consent status was unverified or expired.",
    requestContext:
      "SELECT user_id, open_rate, click_rate\nFROM marketing.leads.engagement_metrics\nWHERE country_code IN ('DE', 'NL', 'BE')\nGROUP BY user_id;",
  },
  {
    id: "req_21",
    timestamp: "2023-11-24T09:48:30Z",
    consumer: "Jack Gale",
    consumerEmail: "jack@fides.ai",
    policy: "HIPAA_COMPLIANCE",
    controlName: "SENSITIVE_DATA_RESTRICTION",
    policyDescription:
      "Restrict all Billing_Data access unless requester has Security_Level_3 and matches Financial_Audit intent header.",
    dataset: "production.billing",
    table: "refunds",
    dataUse: "Marketing",
    system: "Snowflake",
    violationReason:
      "User Jack Gale accessed refund records containing patient billing details for marketing analysis without HIPAA clearance.",
    requestContext:
      "SELECT refund_id, patient_id, refund_amount, reason\nFROM production.billing.refunds\nWHERE refund_date > '2023-10-01';",
  },
  {
    id: "req_22",
    timestamp: "2023-11-24T09:30:00Z",
    consumer: "Data-Science-SA",
    consumerEmail: "ds@internal",
    policy: "PII_SECURITY",
    controlName: "PII_ACCESS_CONTROL",
    policyDescription:
      "Prevent any service account from accessing PII columns without explicit data use declaration.",
    dataset: "analytics.users",
    table: "behavioral_events",
    dataUse: "Identity",
    system: "BigQuery",
    violationReason:
      "Data science service account accessed behavioral event logs containing user fingerprints without a declared identity data use purpose.",
    requestContext:
      "SELECT user_id, browser_fingerprint, session_duration\nFROM analytics.users.behavioral_events\nSAMPLE (10 PERCENT);",
  },
  {
    id: "req_23",
    timestamp: "2023-11-24T09:15:18Z",
    consumer: "Sarah Chen",
    consumerEmail: "sarah@fides.ai",
    policy: "CCPA_RESTRICT",
    controlName: "CROSS_BORDER_DATA_FLOW",
    policyDescription:
      "Block cross-border data transfers for California residents unless explicit consent is recorded.",
    dataset: "external.leads",
    table: "ad_conversions",
    dataUse: "Sales",
    system: "PostgreSQL",
    violationReason:
      "User Sarah Chen exported California ad conversion data to an external analytics vendor without verified CCPA consent.",
    requestContext:
      "SELECT conversion_id, user_email, campaign_source\nFROM external.leads.ad_conversions\nWHERE user_state = 'CA'\nAND conversion_date > '2023-11-01';",
  },
  {
    id: "req_24",
    timestamp: "2023-11-24T08:55:40Z",
    consumer: "Marketing-Service",
    consumerEmail: "service@internal",
    policy: "PII_SHIELD",
    controlName: "CUSTOMER_DATA_MASKING",
    policyDescription:
      "Require data masking for all customer profile queries outside of the production support context.",
    dataset: "customer.profiles",
    table: "loyalty_accounts",
    dataUse: "Marketing",
    system: "Snowflake",
    violationReason:
      "Marketing service accessed unmasked loyalty account data including points balance and tier status for campaign targeting.",
    requestContext:
      "SELECT customer_id, loyalty_tier, points_balance\nFROM customer.profiles.loyalty_accounts\nWHERE loyalty_tier = 'PLATINUM';",
  },
  {
    id: "req_25",
    timestamp: "2023-11-24T08:30:05Z",
    consumer: "Compliance-Bot",
    consumerEmail: "compliance@internal",
    policy: "GDPR_CONSENT",
    controlName: "CONSENT_VERIFICATION",
    policyDescription:
      "Verify active consent records before allowing marketing data access for EU residents.",
    dataset: "marketing.leads",
    table: "retargeting_pool",
    dataUse: "Marketing",
    system: "Redshift",
    violationReason:
      "Compliance bot detected retargeting pool query against EU users whose consent records were revoked or never collected.",
    requestContext:
      "SELECT user_id, last_visit_url, retarget_score\nFROM marketing.leads.retargeting_pool\nWHERE region = 'EU'\nAND consent_status != 'active';",
  },
];

export const POLICY_OPTIONS = [
  { label: "HIPAA_COMPLIANCE", value: "HIPAA_COMPLIANCE" },
  { label: "PII_SECURITY", value: "PII_SECURITY" },
  { label: "CCPA_RESTRICT", value: "CCPA_RESTRICT" },
  { label: "PII_SHIELD", value: "PII_SHIELD" },
  { label: "GDPR_CONSENT", value: "GDPR_CONSENT" },
];

export const DATA_USE_OPTIONS = [
  { label: "Marketing", value: "Marketing" },
  { label: "Identity", value: "Identity" },
  { label: "Sales", value: "Sales" },
];

export const TIME_RANGE_OPTIONS = [
  { label: "Last 24 hours", value: "24h" },
  { label: "Last 7 days", value: "7d" },
  { label: "Last 30 days", value: "30d" },
];

// Summary card enrichment data
export const MOCK_VIOLATION_TREND = "-18%";
export const MOCK_VIOLATION_RATE_TREND = "+2.1%";
export const MOCK_TOP_VIOLATED_POLICIES = [
  { name: "HIPAA_COMPLIANCE", count: 15 },
  { name: "PII_SECURITY", count: 12 },
  { name: "CCPA_RESTRICT", count: 10 },
];
export const MOCK_TOP_DATA_USES = [
  { label: "Marketing", percent: 37 },
  { label: "Identity", percent: 27 },
  { label: "Sales", percent: 22 },
  { label: "Operations", percent: 14 },
];
export const MOCK_VIOLATION_STATUS = { blocked: 15, flagged: 8, allowed: 4 };
export const MOCK_CONSUMER_DATA_USES = ["Marketing", "Identity", "Sales"];
