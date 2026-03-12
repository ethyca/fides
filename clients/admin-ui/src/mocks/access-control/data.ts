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

export const policyViolationsData: PolicyViolationAggregate[] = [
  {
    policy: "Marketing Data Policy",
    control: "No PII for third-party advertising",
    violation_count: 34,
    last_violation: "2026-03-11T14:23:00Z",
  },
  {
    policy: "Marketing Data Policy",
    control: "Consent required for email targeting",
    violation_count: 28,
    last_violation: "2026-03-11T12:15:00Z",
  },
  {
    policy: "Data Retention Policy",
    control: "Delete user data after 90 days",
    violation_count: 22,
    last_violation: "2026-03-10T18:45:00Z",
  },
  {
    policy: "Access Control Policy",
    control: "No cross-region data transfer without approval",
    violation_count: 15,
    last_violation: "2026-03-10T09:30:00Z",
  },
  {
    policy: "PII Protection Policy",
    control: "Mask SSN in non-production environments",
    violation_count: 6,
    last_violation: "2026-03-09T22:10:00Z",
  },
];

export const policyViolationLogsData: PolicyViolationLog[] = [
  {
    timestamp: "2026-03-11T14:23:00Z",
    consumer: "Analytics Service",
    policy: "Marketing Data Policy",
    dataset: "postgres.public.users",
    data_use: "marketing.advertising.third_party.targeted",
  },
  {
    timestamp: "2026-03-11T13:55:00Z",
    consumer: "Marketing Pipeline",
    policy: "Marketing Data Policy",
    dataset: "postgres.public.email_preferences",
    data_use: "marketing.advertising.first_party",
  },
  {
    timestamp: "2026-03-11T12:15:00Z",
    consumer: "Marketing Pipeline",
    policy: "Marketing Data Policy",
    dataset: "postgres.public.users",
    data_use: "marketing.communications",
  },
  {
    timestamp: "2026-03-10T18:45:00Z",
    consumer: "Data Warehouse ETL",
    policy: "Data Retention Policy",
    dataset: "postgres.public.order_history",
    data_use: "functional.service.improve",
  },
  {
    timestamp: "2026-03-10T16:30:00Z",
    consumer: "Analytics Service",
    policy: "Marketing Data Policy",
    dataset: "postgres.public.page_views",
    data_use: "marketing.advertising.third_party",
  },
  {
    timestamp: "2026-03-10T09:30:00Z",
    consumer: "Customer Support Bot",
    policy: "Access Control Policy",
    dataset: "postgres.public.support_tickets",
    data_use: "functional.service",
  },
  {
    timestamp: "2026-03-09T22:10:00Z",
    consumer: "Data Warehouse ETL",
    policy: "PII Protection Policy",
    dataset: "postgres.public.users",
    data_use: "functional.service.improve",
  },
];
