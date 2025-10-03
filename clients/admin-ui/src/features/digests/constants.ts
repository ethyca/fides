import { DigestType, MessagingMethod } from "~/types/api";

export const DIGEST_TYPE_LABELS: Record<DigestType, string> = {
  [DigestType.MANUAL_TASKS]: "Manual Tasks",
  [DigestType.PRIVACY_REQUESTS]: "Privacy Requests",
};

export const MESSAGING_METHOD_LABELS: Record<MessagingMethod, string> = {
  [MessagingMethod.EMAIL]: "Email",
  [MessagingMethod.SMS]: "SMS",
};

export const DEFAULT_CRON_EXPRESSION = "0 9 * * 1"; // Weekly on Monday at 9 AM UTC
export const DEFAULT_TIMEZONE = "UTC"; // All digests run in UTC timezone

// For Phase 1, we only support manual tasks
export const SUPPORTED_DIGEST_TYPES = [DigestType.MANUAL_TASKS];
