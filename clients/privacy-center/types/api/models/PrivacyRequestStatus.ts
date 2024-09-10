/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Enum for privacy request statuses, reflecting where they are in the Privacy Request Lifecycle
 */
export enum PrivacyRequestStatus {
  IDENTITY_UNVERIFIED = "identity_unverified",
  REQUIRES_INPUT = "requires_input",
  PENDING = "pending",
  APPROVED = "approved",
  DENIED = "denied",
  IN_PROCESSING = "in_processing",
  COMPLETE = "complete",
  PAUSED = "paused",
  AWAITING_EMAIL_SEND = "awaiting_email_send",
  CANCELED = "canceled",
  ERROR = "error",
}
