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
  REQUIRES_MANUAL_FINALIZATION = "requires_manual_finalization",
  CANCELED = "canceled",
  ERROR = "error",
  DUPLICATE = "duplicate",
  AWAITING_PRE_APPROVAL = "awaiting_pre_approval",
  PRE_APPROVAL_NOT_ELIGIBLE = "pre_approval_not_eligible",
}
