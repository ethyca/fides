/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Enum for messaging action type
 */
export enum MessagingActionType {
  CONSENT_REQUEST = "consent_request",
  SUBJECT_IDENTITY_VERIFICATION = "subject_identity_verification",
  CONSENT_REQUEST_EMAIL_FULFILLMENT = "consent_request_email_fulfillment",
  MESSAGE_ERASURE_FULFILLMENT = "message_erasure_fulfillment",
  PRIVACY_REQUEST_ERROR_NOTIFICATION = "privacy_request_error_notification",
  PRIVACY_REQUEST_RECEIPT = "privacy_request_receipt",
  PRIVACY_REQUEST_COMPLETE_ACCESS = "privacy_request_complete_access",
  PRIVACY_REQUEST_COMPLETE_DELETION = "privacy_request_complete_deletion",
  PRIVACY_REQUEST_REVIEW_DENY = "privacy_request_review_deny",
  PRIVACY_REQUEST_REVIEW_APPROVE = "privacy_request_review_approve",
  USER_INVITE = "user_invite",
  TEST_MESSAGE = "test_message",
}
