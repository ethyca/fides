import type {
  DataConsumerRequestPoint,
  DataConsumerRequestsResponse,
  DataConsumerSummary,
  PolicyViolationAggregate,
} from "~/features/access-control/types";
import { pickInterval } from "fidesui";

const sumField = (
  items: DataConsumerRequestPoint[],
  field: "requests" | "violations",
) => items.reduce((sum, item) => sum + item[field], 0);

const TOP_POLICIES = [
  { name: "HIPAA_COMPLIANCE", count: 15 },
  { name: "PII_SECURITY", count: 12 },
  { name: "CCPA_RESTRICT", count: 10 },
];

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

const seededRandom = (seed: number) => {
  let s = seed;
  return () => {
    s = (s * 16807 + 0) % 2147483647;
    return (s - 1) / 2147483646;
  };
};

export const generateChartData = (
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
    requests: 3 + Math.floor(rand() * 8),
    violations: Math.floor(rand() * 4),
  }));

  return {
    violations: sumField(buckets, "violations"),
    total_requests: sumField(buckets, "requests"),
    trend: -0.08,
    top_policies: TOP_POLICIES,
    total_policies: POLICIES.length,
    items: buckets,
  };
};
