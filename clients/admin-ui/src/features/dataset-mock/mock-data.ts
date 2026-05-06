/**
 * Invented data fixtures powering the /dataset-mock prototype pages.
 *
 * This file is intentionally not type-bound to the real Dataset / Collection
 * models. The shape here is what the mocks need to render the future-state
 * PRD requirements; nothing on this page hits the API.
 */

export type HealthBadge =
  // Blocking
  | "needs-dsr-wiring"
  | "connection-failed"
  | "connection-untested"
  // Warning
  | "schema-drifted"
  | "monitor-disabled"
  | "no-successful-dsr"
  // Informational
  | "manual"
  | "healthy";

export const BLOCKING_BADGES: ReadonlySet<HealthBadge> = new Set([
  "needs-dsr-wiring",
  "connection-failed",
  "connection-untested",
]);

export const WARNING_BADGES: ReadonlySet<HealthBadge> = new Set([
  "schema-drifted",
  "monitor-disabled",
  "no-successful-dsr",
]);

export const HEALTH_BADGE_LABELS: Record<HealthBadge, string> = {
  "needs-dsr-wiring": "Needs DSR wiring",
  "connection-failed": "Connection failed",
  "connection-untested": "Connection untested",
  "schema-drifted": "Schema drifted",
  "monitor-disabled": "Monitor disabled",
  "no-successful-dsr": "No successful DSR",
  manual: "Manual",
  healthy: "Healthy",
};

export type CollectionStatus = "ok" | "needs-dsr-wiring" | "skipped";

export interface MockCollection {
  name: string;
  description: string;
  fieldCount: number;
  approvedFieldPct: number;
  status: CollectionStatus;
  hasIdentity: boolean;
  reason?: string;
}

export interface MockDataset {
  fidesKey: string;
  name: string;
  description: string;
  integration: string | null; // null → manual
  healthBadges: HealthBadge[];
  collectionCount: number;
  totalFields: number;
  approvedFieldPct: number;
  lastClassifiedAt: string; // ISO-ish display string
  // Provenance (for §2)
  sourceMonitor: string | null;
  approvedBy: string | null;
  approvedAt: string | null;
  approvalAction: string | null;
  linkedActionCenterItems: number;
  // Collections (for §6 + §3)
  collections: MockCollection[];
}

const LEGACY_ORDERS_COLLECTIONS: MockCollection[] = [
  { name: "users", description: "Customer profile records.", fieldCount: 12, approvedFieldPct: 75, status: "needs-dsr-wiring", hasIdentity: false, reason: "No identity field declared" },
  { name: "orders", description: "Order header records, one per checkout.", fieldCount: 14, approvedFieldPct: 71, status: "ok", hasIdentity: true },
  { name: "order_items", description: "Line items inside each order.", fieldCount: 8, approvedFieldPct: 88, status: "ok", hasIdentity: false },
  { name: "addresses", description: "Billing and shipping addresses.", fieldCount: 9, approvedFieldPct: 33, status: "needs-dsr-wiring", hasIdentity: false, reason: "FK references unreachable user_id" },
  { name: "payments", description: "Captured payment records.", fieldCount: 7, approvedFieldPct: 86, status: "ok", hasIdentity: false },
  { name: "refunds", description: "Refund and chargeback records.", fieldCount: 5, approvedFieldPct: 100, status: "ok", hasIdentity: false },
  { name: "carts", description: "Pre-checkout shopping cart state.", fieldCount: 6, approvedFieldPct: 0, status: "skipped", hasIdentity: false, reason: "skip_processing = true (legacy table)" },
  { name: "audit_log", description: "Order-system audit trail.", fieldCount: 4, approvedFieldPct: 25, status: "skipped", hasIdentity: false, reason: "skip_processing = true" },
  { name: "promotions", description: "Promo codes redeemed per order.", fieldCount: 3, approvedFieldPct: 100, status: "ok", hasIdentity: false },
  { name: "shipments", description: "Shipping events and tracking numbers.", fieldCount: 3, approvedFieldPct: 67, status: "ok", hasIdentity: false },
  { name: "tax_records", description: "Tax breakdown per order.", fieldCount: 2, approvedFieldPct: 0, status: "ok", hasIdentity: false },
];

const placeholderCollections = (count: number, fieldCount: number): MockCollection[] =>
  Array.from({ length: count }, (_, i) => ({
    name: `collection_${i + 1}`,
    description: "—",
    fieldCount: Math.round(fieldCount / count),
    approvedFieldPct: 80,
    status: "ok" as CollectionStatus,
    hasIdentity: i === 0,
  }));

export const MOCK_DATASETS: MockDataset[] = [
  {
    fidesKey: "legacy_orders_pg",
    name: "Legacy Orders (Postgres)",
    description:
      "Order, customer, and payment data from the pre-migration billing platform.",
    integration: "postgres-prod-replica",
    healthBadges: ["needs-dsr-wiring", "connection-failed"],
    collectionCount: 11,
    totalFields: 73,
    approvedFieldPct: 41,
    lastClassifiedAt: "Apr 12, 2026",
    sourceMonitor: "legacy_postgres_monitor",
    approvedBy: "Akshay Kumar",
    approvedAt: "Apr 30, 2026",
    approvalAction: "Quick approval",
    linkedActionCenterItems: 4,
    collections: LEGACY_ORDERS_COLLECTIONS,
  },
  {
    fidesKey: "customer_360_warehouse",
    name: "Customer 360 Warehouse",
    description:
      "Unified customer profile dataset shared with marketing and support.",
    integration: "snowflake-c360",
    healthBadges: ["connection-untested"],
    collectionCount: 8,
    totalFields: 142,
    approvedFieldPct: 88,
    lastClassifiedAt: "Apr 28, 2026",
    sourceMonitor: "snowflake_c360_monitor",
    approvedBy: "Daniel Reyes",
    approvedAt: "Apr 14, 2026",
    approvalAction: "Bulk approve",
    linkedActionCenterItems: 1,
    collections: placeholderCollections(8, 142),
  },
  {
    fidesKey: "clickstream_events",
    name: "Clickstream Events",
    description:
      "Web and mobile event stream landing in the analytics lakehouse.",
    integration: "bigquery-events",
    healthBadges: ["schema-drifted", "no-successful-dsr"],
    collectionCount: 4,
    totalFields: 56,
    approvedFieldPct: 64,
    lastClassifiedAt: "Mar 22, 2026",
    sourceMonitor: "events_bigquery_monitor",
    approvedBy: "Victoria Ng",
    approvedAt: "Mar 22, 2026",
    approvalAction: "Quick approval",
    linkedActionCenterItems: 2,
    collections: placeholderCollections(4, 56),
  },
  {
    fidesKey: "analytics_replica",
    name: "Analytics Replica",
    description: "Read replica used by the analytics team for ad-hoc queries.",
    integration: "postgres-analytics",
    healthBadges: ["monitor-disabled"],
    collectionCount: 6,
    totalFields: 49,
    approvedFieldPct: 73,
    lastClassifiedAt: "Feb 04, 2026",
    sourceMonitor: "analytics_replica_monitor",
    approvedBy: "Adam Ostrowski",
    approvedAt: "Feb 04, 2026",
    approvalAction: "Manual approval",
    linkedActionCenterItems: 1,
    collections: placeholderCollections(6, 49),
  },
  {
    fidesKey: "acme_marketing_warehouse",
    name: "Acme Marketing Warehouse",
    description:
      "Centralized marketing reporting warehouse with campaign attribution data.",
    integration: "snowflake-marketing",
    healthBadges: ["healthy"],
    collectionCount: 5,
    totalFields: 87,
    approvedFieldPct: 96,
    lastClassifiedAt: "May 02, 2026",
    sourceMonitor: "marketing_snowflake_monitor",
    approvedBy: "Akshay Kumar",
    approvedAt: "May 01, 2026",
    approvalAction: "Bulk approve",
    linkedActionCenterItems: 3,
    collections: placeholderCollections(5, 87),
  },
  {
    fidesKey: "manual_pii_export",
    name: "Manual PII Export",
    description:
      "Spreadsheet-driven PII export from the HR system, processed via webhook.",
    integration: null,
    healthBadges: ["manual"],
    collectionCount: 2,
    totalFields: 12,
    approvedFieldPct: 100,
    lastClassifiedAt: "—",
    sourceMonitor: null,
    approvedBy: null,
    approvedAt: null,
    approvalAction: null,
    linkedActionCenterItems: 0,
    collections: placeholderCollections(2, 12),
  },
];

export const findDatasetByKey = (fidesKey: string): MockDataset | undefined =>
  MOCK_DATASETS.find((d) => d.fidesKey === fidesKey);

/**
 * Sort: blocking-badge count first (more = higher), then warning-badge count,
 * then name. Matches PRD §1.
 */
export const sortDatasetsByHealth = (datasets: MockDataset[]): MockDataset[] =>
  [...datasets].sort((a, b) => {
    const aBlocking = a.healthBadges.filter((b_) =>
      BLOCKING_BADGES.has(b_),
    ).length;
    const bBlocking = b.healthBadges.filter((b_) =>
      BLOCKING_BADGES.has(b_),
    ).length;
    if (aBlocking !== bBlocking) {
      return bBlocking - aBlocking;
    }
    const aWarning = a.healthBadges.filter((b_) =>
      WARNING_BADGES.has(b_),
    ).length;
    const bWarning = b.healthBadges.filter((b_) =>
      WARNING_BADGES.has(b_),
    ).length;
    if (aWarning !== bWarning) {
      return bWarning - aWarning;
    }
    return a.name.localeCompare(b.name);
  });
