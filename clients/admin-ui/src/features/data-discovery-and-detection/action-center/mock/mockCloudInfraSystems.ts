import {
  connectionLogoFromKey,
  type ConnectionLogoSource,
} from "~/features/datastore-connections/ConnectionTypeLogo";

/**
 * How a system that resources can be assigned to should be represented in the
 * tree / tags. Drives which leading icon is shown:
 * - COMPASS   → a known inventory system (Compass match) with a connector logo
 * - SUGGESTED → a Fides-suggested staged business application (sparkle icon)
 * - GENERIC   → a user-created system / no Compass match (generic system icon)
 */
export enum MockSystemKind {
  COMPASS = "compass",
  SUGGESTED = "suggested",
  GENERIC = "generic",
}

export interface MockCloudInfraSystem {
  fides_key: string;
  name: string;
  kind: MockSystemKind;
  /** Connector-logo filename (without path) — COMPASS systems only. */
  logoKey?: string;
}

export const MOCK_CLOUD_INFRA_SYSTEMS: MockCloudInfraSystem[] = [
  // Fides-suggested business applications — staged systems Fides proposes
  // based on the underlying AWS resources. Shown with a sparkle icon.
  {
    fides_key: "marketing_assets",
    name: "Marketing Assets",
    kind: MockSystemKind.SUGGESTED,
  },
  {
    fides_key: "customer_receipts",
    name: "Customer Receipts",
    kind: MockSystemKind.SUGGESTED,
  },
  {
    fides_key: "order_management",
    name: "Order Management",
    kind: MockSystemKind.SUGGESTED,
  },
  {
    fides_key: "customer_database",
    name: "Customer Database",
    kind: MockSystemKind.SUGGESTED,
  },
  // Known inventory systems (Compass matches) — shown with their connector logo.
  {
    fides_key: "snowflake",
    name: "Snowflake",
    kind: MockSystemKind.COMPASS,
    logoKey: "snowflake",
  },
  {
    fides_key: "salesforce",
    name: "Salesforce",
    kind: MockSystemKind.COMPASS,
    logoKey: "salesforce",
  },
  {
    fides_key: "okta",
    name: "Okta",
    kind: MockSystemKind.COMPASS,
    logoKey: "okta",
  },
  {
    fides_key: "jira",
    name: "Jira",
    kind: MockSystemKind.COMPASS,
    logoKey: "jira",
  },
];

const SYSTEM_BY_KEY = new Map(
  MOCK_CLOUD_INFRA_SYSTEMS.map((system) => [system.fides_key, system]),
);

export const getMockSystem = (
  fidesKey?: string | number | null,
): MockCloudInfraSystem | undefined =>
  fidesKey === null || fidesKey === undefined
    ? undefined
    : SYSTEM_BY_KEY.get(String(fidesKey));

/**
 * Logo for a known inventory (Compass) system. Returns undefined for suggested,
 * generic, or unknown systems so callers fall back to the appropriate icon.
 */
export const getMockSystemLogoSource = (
  fidesKey?: string | number | null,
): ConnectionLogoSource | undefined => {
  const system = getMockSystem(fidesKey);
  return system?.kind === MockSystemKind.COMPASS && system.logoKey
    ? connectionLogoFromKey(system.logoKey)
    : undefined;
};

/** True for Fides-suggested staged business applications (sparkle icon). */
export const isSuggestedSystem = (fidesKey?: string | number | null): boolean =>
  getMockSystem(fidesKey)?.kind === MockSystemKind.SUGGESTED;

/**
 * True for a system that isn't in the catalog — i.e. a user-created system not
 * matched to Compass/inventory or a suggestion (gets a green-dot "new" badge).
 */
export const isNewSystem = (fidesKey?: string | number | null): boolean =>
  fidesKey !== null && fidesKey !== undefined && !getMockSystem(fidesKey);

/**
 * Flat value/label option list for the assign dropdown. Labels are kept as
 * plain strings so the stored selection (labelInValue) renders correctly in the
 * tree and tags; icons are layered on via optionRender/labelRender.
 */
export const MOCK_SYSTEM_SELECT_OPTIONS = MOCK_CLOUD_INFRA_SYSTEMS.map(
  (system) => ({ label: system.name, value: system.fides_key }),
);

/**
 * Resources that arrive from the scan already mapped to a Fides-suggested (or
 * known inventory) system, so the tree shows those system groupings by default.
 * Keyed by resource urn → system fides_keys.
 */
export const DEFAULT_RESOURCE_SYSTEM_ASSIGNMENTS: Record<string, string[]> = {
  "arn:aws:s3:::cookie-house-marketing-assets": ["marketing_assets"],
  "arn:aws:s3:::cookie-house-receipts": ["customer_receipts"],
  "arn:aws:rds:us-east-1:123456789012:db:orders-prod": ["order_management"],
  "arn:aws:lambda:us-east-1:123456789012:function:order-events-router": [
    "order_management",
  ],
  "arn:aws:rds:us-east-1:123456789012:db:customers-prod": ["customer_database"],
  "arn:aws:rds:eu-west-1:210987654321:db:eu-customers": ["customer_database"],
  // A known inventory (Compass) system, to show the logo treatment by default.
  "arn:aws:redshift:us-west-2:123456789012:cluster:analytics-warehouse": [
    "snowflake",
  ],
};

/** Build assign-option objects for a resource's default system assignments. */
export const getDefaultAssignedSystems = (
  urn: string,
): { label: string; value: string }[] =>
  (DEFAULT_RESOURCE_SYSTEM_ASSIGNMENTS[urn] ?? []).map((fidesKey) => ({
    value: fidesKey,
    label: getMockSystem(fidesKey)?.name ?? fidesKey,
  }));
