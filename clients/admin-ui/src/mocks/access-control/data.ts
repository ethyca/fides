import type {
  DataConsumerRequestPoint,
  DataConsumerRequestsResponse,
  DataConsumerSummary,
  PolicyViolationAggregate,
  PolicyViolationLog,
} from "~/features/access-control/types";
import { pickInterval } from "~/features/access-control/utils";

const sumField = (
  items: DataConsumerRequestPoint[],
  field: "requests" | "violations",
) => items.reduce((sum, item) => sum + item[field], 0);

export const generateChartData = (
  startDate: string,
  endDate: string,
  requestRange: [number, number] = [10, 40],
  violationRange: [number, number] = [0, 8],
): DataConsumerRequestsResponse => {
  const startMs = new Date(startDate).getTime();
  const endMs = new Date(endDate).getTime();
  const interval = pickInterval(startMs, endMs);
  const flooredStart = Math.floor(startMs / interval) * interval;
  const count = Math.max(1, Math.ceil((endMs - flooredStart) / interval));
  const items = Array.from({ length: count }, (_, i) => ({
    timestamp: new Date(flooredStart + i * interval).toISOString(),
    requests:
      Math.floor(Math.random() * requestRange[1]) + requestRange[0],
    violations:
      Math.floor(Math.random() * violationRange[1]) + violationRange[0],
  }));
  return {
    violations: sumField(items, "violations"),
    total_requests: sumField(items, "requests"),
    items,
  };
};

export const dataConsumersByViolationsData: DataConsumerSummary[] = [
  { name: "Analytics Service", requests: 620, violations: 34 },
  { name: "Marketing Pipeline", requests: 485, violations: 28 },
  { name: "Data Warehouse ETL", requests: 410, violations: 22 },
  { name: "Customer Support Bot", requests: 155, violations: 12 },
  { name: "Recommendation Engine", requests: 128, violations: 9 },
];

export const POLICIES = [
  "Marketing Data Policy",
  "Data Retention Policy",
  "Access Control Policy",
  "PII Protection Policy",
  "Third-Party Sharing Policy",
  "Employee Data Policy",
  "Financial Data Policy",
  "Health Data Policy",
];

const CONTROLS: Record<string, string[]> = {
  "Marketing Data Policy": [
    "No PII for third-party advertising",
    "Consent required for email targeting",
    "No behavioral profiling without opt-in",
    "Limit data collection to stated purpose",
    "No sharing with unvetted ad networks",
    "Anonymize analytics data before export",
  ],
  "Data Retention Policy": [
    "Delete user data after 90 days",
    "Purge inactive accounts annually",
    "Archive logs after 30 days",
    "Remove payment data after transaction",
  ],
  "Access Control Policy": [
    "No cross-region data transfer without approval",
    "Require MFA for sensitive data access",
    "Restrict admin access to production",
    "Enforce least-privilege for service accounts",
    "Log all access to PII fields",
  ],
  "PII Protection Policy": [
    "Mask SSN in non-production environments",
    "Encrypt PII at rest and in transit",
    "No PII in application logs",
    "Tokenize credit card numbers",
    "Redact email in public-facing exports",
  ],
  "Third-Party Sharing Policy": [
    "DPA required before data sharing",
    "No sharing of biometric data",
    "Audit third-party access quarterly",
    "Restrict fields shared with vendors",
  ],
  "Employee Data Policy": [
    "HR data accessible only to HR systems",
    "No employee data in analytics pipelines",
    "Separate employee PII from product data",
  ],
  "Financial Data Policy": [
    "PCI-DSS compliance for card data",
    "No raw financial data in staging",
    "Encrypt account numbers end-to-end",
    "Restrict transaction data to billing service",
  ],
  "Health Data Policy": [
    "HIPAA compliance for health records",
    "No health data in marketing contexts",
    "De-identify health data for research",
    "Restrict access to authorized providers",
  ],
};

const generateViolations = (): PolicyViolationAggregate[] => {
  const baseTime = new Date("2026-03-11T14:23:00Z").getTime();

  return POLICIES.flatMap((policy) =>
    CONTROLS[policy].map((control, i) => ({
      policy,
      control,
      violation_count: Math.floor(Math.random() * 40) + 2,
      last_violation: new Date(baseTime - i * 2 * 60 * 60 * 1000).toISOString(),
    })),
  ).sort((a, b) => b.violation_count - a.violation_count);
};

export const policyViolationsData: PolicyViolationAggregate[] =
  generateViolations();

export const LOG_CONSUMERS = [
  "Analytics Service",
  "Marketing Pipeline",
  "Data Warehouse ETL",
  "Customer Support Bot",
  "Recommendation Engine",
  "Billing Service",
  "HR Portal",
  "Research Platform",
];

export const LOG_DATASETS = [
  "postgres.public.users",
  "postgres.public.email_preferences",
  "postgres.public.order_history",
  "postgres.public.page_views",
  "postgres.public.support_tickets",
  "postgres.public.transactions",
  "postgres.public.employee_records",
  "postgres.public.health_records",
  "postgres.public.payment_methods",
  "snowflake.analytics.user_events",
  "snowflake.analytics.sessions",
  "redshift.warehouse.customer_profiles",
];

export const LOG_DATA_USES = [
  "marketing.advertising.third_party.targeted",
  "marketing.advertising.first_party",
  "marketing.communications",
  "functional.service.improve",
  "functional.service",
  "essential.service.operations",
  "personalize.content",
  "analytics.reporting",
  "third_party_sharing.legal_obligation",
  "collect.provide",
];

const POLICY_DESCRIPTIONS: Record<string, string> = {
  "Marketing Data Policy":
    "Governs how customer data may be used for marketing purposes, including advertising, targeting, and profiling.",
  "Data Retention Policy":
    "Defines retention periods and deletion schedules for various categories of personal data.",
  "Access Control Policy":
    "Controls who can access sensitive data and under what conditions, including cross-region transfers.",
  "PII Protection Policy":
    "Ensures personally identifiable information is encrypted, masked, or tokenized in all environments.",
  "Third-Party Sharing Policy":
    "Regulates data sharing with external vendors, requiring DPAs and limiting shared fields.",
  "Employee Data Policy":
    "Protects employee personal data by restricting access to HR systems only.",
  "Financial Data Policy":
    "Enforces PCI-DSS compliance and encryption for all financial and payment data.",
  "Health Data Policy":
    "Ensures HIPAA compliance and de-identification for health-related records.",
};

const SQL_STATEMENTS = [
  "SELECT u.email, u.name, u.phone\nFROM users u\nJOIN orders o ON u.id = o.user_id\nWHERE o.created_at > NOW() - INTERVAL '30 days'",
  "SELECT email, ssn, date_of_birth\nFROM employee_records\nWHERE department = 'Engineering'",
  "SELECT card_number, expiry_date, cvv\nFROM payment_methods\nWHERE user_id IN (SELECT id FROM users WHERE region = 'EU')",
  "SELECT ip_address, user_agent, page_url\nFROM page_views\nWHERE session_id = 'abc-123'",
  "SELECT health_condition, medication, provider\nFROM health_records\nJOIN users ON health_records.patient_id = users.id",
  "SELECT t.amount, t.merchant, u.name\nFROM transactions t\nJOIN users u ON t.user_id = u.id\nWHERE t.amount > 1000",
  "SELECT email, preferences, opt_out_date\nFROM email_preferences\nWHERE marketing_consent = false",
  "SELECT c.name, c.email, s.ticket_text\nFROM support_tickets s\nJOIN users c ON s.customer_id = c.id\nWHERE s.status = 'open'",
  "SELECT event_type, user_id, properties\nFROM user_events\nWHERE event_type = 'purchase'\nAND timestamp > '2026-01-01'",
  "SELECT name, email, salary, manager\nFROM employee_records\nORDER BY salary DESC\nLIMIT 100",
];

const AI_REASONS = [
  "Query accesses PII fields (email, phone) without applying column-level masking required by the policy.",
  "Cross-region data transfer detected: EU user data accessed from US-based service without approval.",
  "SSN field accessed in non-production environment without required masking transformation.",
  "Credit card data queried without PCI-DSS compliant tokenization in the result set.",
  "Health records joined with user identity data, violating de-identification requirements.",
  "Marketing consent status ignored — query targets users who have opted out of communications.",
  "Employee salary data accessed by non-HR service account, violating least-privilege requirements.",
  "Third-party vendor service accessing customer data without a registered Data Processing Agreement.",
  "Financial transaction data exposed to staging environment without end-to-end encryption.",
  "Behavioral profiling query detected without required user opt-in consent verification.",
  "Data retention violation: query accesses records older than the 90-day retention window.",
  "Bulk export of PII fields detected without anonymization transformation applied.",
];

const seededRandom = (seed: number) => {
  let s = seed;
  return () => {
    s = (s * 16807 + 0) % 2147483647;
    return (s - 1) / 2147483646;
  };
};

const generateStableLogs = (): PolicyViolationLog[] => {
  const now = new Date("2026-03-13T12:00:00Z").getTime();
  const allPolicies = Object.keys(CONTROLS);
  const rand = seededRandom(42);
  const LOG_COUNT = 2000;

  return Array.from({ length: LOG_COUNT }, (_, i) => {
    const gap = 3 * 60_000 + Math.floor(rand() * 12 * 60_000);
    const consumer = LOG_CONSUMERS[Math.floor(rand() * LOG_CONSUMERS.length)];
    const policy = allPolicies[Math.floor(rand() * allPolicies.length)];
    return {
      id: `viol-${String(i).padStart(4, "0")}`,
      timestamp: new Date(now - i * gap).toISOString(),
      consumer,
      consumer_email: `${consumer.toLowerCase().replace(/\s+/g, "-")}@company.com`,
      policy,
      policy_description: POLICY_DESCRIPTIONS[policy] ?? "",
      dataset: LOG_DATASETS[Math.floor(rand() * LOG_DATASETS.length)],
      data_use: LOG_DATA_USES[Math.floor(rand() * LOG_DATA_USES.length)],
      sql_statement: SQL_STATEMENTS[Math.floor(rand() * SQL_STATEMENTS.length)],
      ai_reason: rand() < 0.7 ? AI_REASONS[Math.floor(rand() * AI_REASONS.length)] : undefined,
    };
  }).sort((a, b) => b.timestamp.localeCompare(a.timestamp));
};

export const allViolationLogs: PolicyViolationLog[] = generateStableLogs();

export interface LogFilters {
  consumer?: string | string[] | null;
  policy?: string | string[] | null;
  dataset?: string | string[] | null;
  data_use?: string | string[] | null;
  start_date?: string | null;
  end_date?: string | null;
}

const matchesFilter = (
  value: string,
  filter: string | string[] | null | undefined,
): boolean => {
  if (!filter) return true;
  return Array.isArray(filter) ? filter.includes(value) : value === filter;
};

export const filterLogs = (
  logs: PolicyViolationLog[],
  filters: LogFilters,
): PolicyViolationLog[] => {
  return logs.filter((log) => {
    if (!matchesFilter(log.consumer, filters.consumer)) return false;
    if (!matchesFilter(log.policy, filters.policy)) return false;
    if (!matchesFilter(log.dataset, filters.dataset)) return false;
    if (!matchesFilter(log.data_use, filters.data_use)) return false;
    if (filters.start_date && log.timestamp < filters.start_date) return false;
    if (filters.end_date && log.timestamp > filters.end_date) return false;
    return true;
  });
};

export const aggregateLogsToChart = (
  logs: PolicyViolationLog[],
  startDate: string,
  endDate: string,
): DataConsumerRequestsResponse => {
  const startMs = new Date(startDate).getTime();
  const endMs = new Date(endDate).getTime();
  const interval = pickInterval(startMs, endMs);
  const flooredStart = Math.floor(startMs / interval) * interval;
  const bucketCount = Math.max(1, Math.ceil((endMs - flooredStart) / interval));
  const rand = seededRandom(7);

  const buckets = Array.from({ length: bucketCount }, (_, i) => ({
    timestamp: new Date(flooredStart + i * interval).toISOString(),
    requests: 0,
    violations: 0,
  }));

  for (const log of logs) {
    const logMs = new Date(log.timestamp).getTime();
    const idx = Math.floor((logMs - flooredStart) / interval);
    if (idx >= 0 && idx < bucketCount) {
      buckets[idx].violations += 1;
      buckets[idx].requests += 3 + Math.floor(rand() * 4);
    }
  }

  return {
    violations: sumField(buckets, "violations"),
    total_requests: sumField(buckets, "requests"),
    items: buckets,
  };
};
