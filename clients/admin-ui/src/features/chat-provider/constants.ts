/**
 * Chat provider types and configuration constants
 */

export const CHAT_PROVIDER_TYPES = {
  SLACK: "slack",
  FIDES: "fides",
} as const;

export const CHAT_PROVIDER_LABELS = {
  [CHAT_PROVIDER_TYPES.SLACK]: "Slack",
  [CHAT_PROVIDER_TYPES.FIDES]: "Fides",
} as const;

export const CHAT_PROVIDER_CONFIG_MAX_WIDTH = 720;

export const SECRET_PLACEHOLDER = "**********";
