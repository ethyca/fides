/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Enum for audit log actions, reflecting what a user did.
 */
export enum AuditLogAction {
  APPROVED = "approved",
  ATTACHMENT_UPLOADED = "attachment_uploaded",
  ATTACHMENT_DELETED = "attachment_deleted",
  ATTACHMENT_RETRIEVED = "attachment_retrieved",
  DENIED = "denied",
  EMAIL_SENT = "email_sent",
  FINISHED = "finished",
}
