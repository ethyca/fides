import type { Key } from "antd/es/table/interface";

// Constants
export const PARENT_KEY = "email_marketing" as const;

// Hardcoded UUIDs for each tree node
export const PARENT_KEY_WITH_UUID = `${PARENT_KEY}-a1b2c3d4-e5f6-7890-abcd-ef1234567890`;

export const TREE_NODES = [
  {
    title: "reward_points",
    key: "reward_points-b2c3d4e5-f6g7-8901-bcde-f23456789012",
  },
  {
    title: "current_account_benefits",
    key: "current_account_benefits-c3d4e5f6-g7h8-9012-cdef-345678901234",
  },
  {
    title: "credit_card_offers",
    key: "credit_card_offers-d4e5f6g7-h8i9-0123-defg-456789012345",
  },
  {
    title: "checking_and_saving_offers",
    key: "checking_and_saving_offers-e5f6g7h8-i9j0-1234-efgh-567890123456",
  },
  {
    title: "credit_monitoring",
    key: "credit_monitoring-f6g7h8i9-j0k1-2345-fghi-678901234567",
  },
  {
    title: "auto_financing",
    key: "auto_financing-g7h8i9j0-k1l2-3456-ghij-789012345678",
  },
];

export const ALL_KEYS: Key[] = [
  PARENT_KEY_WITH_UUID,
  ...TREE_NODES.map((node) => node.key),
];
export const INITIAL_EXPANDED_KEYS: Key[] = [PARENT_KEY_WITH_UUID];

// Experience configuration defaults
export const EXPERIENCE_DEFAULTS = {
  REGION: "us_ca",
  COMPONENT: "overlay",
  SHOW_DISABLED: false,
  SYSTEMS_APPLICABLE: true,
} as const;
