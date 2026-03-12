import type {
  DataConsumerRequestPoint,
  DataConsumerRequestsResponse,
  DataConsumerSummary,
  PolicyViolationAggregate,
  PolicyViolationLog,
} from "~/features/access-control/types";

const generateData = (
  count: number,
  msPerPoint: number,
  requestRange: [number, number],
  violationRange: [number, number],
): DataConsumerRequestPoint[] => {
  const now = new Date("2026-03-12T12:00:00Z");
  return Array.from({ length: count }, (_, index) => ({
    timestamp: new Date(
      now.getTime() - (count - 1 - index) * msPerPoint,
    ).toISOString(),
    requests: Math.floor(Math.random() * requestRange[1]) + requestRange[0],
    violations:
      Math.floor(Math.random() * violationRange[1]) + violationRange[0],
  }));
};

const sumField = (
  items: DataConsumerRequestPoint[],
  field: "requests" | "violations",
) => items.reduce((sum, item) => sum + item[field], 0);

const HOUR_MS = 60 * 60 * 1000;
const DAY_MS = 24 * HOUR_MS;

const items24h = generateData(24, HOUR_MS, [10, 40], [0, 8]);
const items7d = generateData(7, DAY_MS, [180, 100], [8, 20]);
const items30d = generateData(30, DAY_MS, [140, 120], [5, 25]);

export const dataConsumerRequestsData: Record<
  string,
  DataConsumerRequestsResponse
> = {
  "24h": {
    violations: sumField(items24h, "violations"),
    total_requests: sumField(items24h, "requests"),
    items: items24h,
  },
  "7d": {
    violations: sumField(items7d, "violations"),
    total_requests: sumField(items7d, "requests"),
    items: items7d,
  },
  "30d": {
    violations: sumField(items30d, "violations"),
    total_requests: sumField(items30d, "requests"),
    items: items30d,
  },
};

export const dataConsumersByViolationsData: DataConsumerSummary[] = [
  { name: "Analytics Service", requests: 620, violations: 34 },
  { name: "Marketing Pipeline", requests: 485, violations: 28 },
  { name: "Data Warehouse ETL", requests: 410, violations: 22 },
  { name: "Customer Support Bot", requests: 155, violations: 12 },
  { name: "Recommendation Engine", requests: 128, violations: 9 },
];

const POLICIES = [
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

const LOG_CONSUMERS = [
  "Analytics Service",
  "Marketing Pipeline",
  "Data Warehouse ETL",
  "Customer Support Bot",
  "Recommendation Engine",
  "Billing Service",
  "HR Portal",
  "Research Platform",
];

const LOG_DATASETS = [
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

const LOG_DATA_USES = [
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

const generateLogs = (): PolicyViolationLog[] => {
  const baseTime = new Date("2026-03-11T14:23:00Z").getTime();
  const allPolicies = Object.keys(CONTROLS);

  return Array.from({ length: 50 }, (_, i) => ({
    timestamp: new Date(baseTime - i * 45 * 60 * 1000).toISOString(),
    consumer: LOG_CONSUMERS[i % LOG_CONSUMERS.length],
    policy: allPolicies[i % allPolicies.length],
    dataset: LOG_DATASETS[i % LOG_DATASETS.length],
    data_use: LOG_DATA_USES[i % LOG_DATA_USES.length],
  }));
};

export const policyViolationLogsData: PolicyViolationLog[] = generateLogs();
