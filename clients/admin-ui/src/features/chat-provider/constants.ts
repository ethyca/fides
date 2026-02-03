/**
 * Chat provider types and configuration constants
 */

export const CHAT_PROVIDER_TYPES = {
  SLACK: "slack",
} as const;

export const CHAT_PROVIDER_LABELS = {
  [CHAT_PROVIDER_TYPES.SLACK]: "Slack",
} as const;

export const CHAT_PROVIDER_CONFIG_MAX_WIDTH = 720;

export const SECRET_PLACEHOLDER = "**********";
