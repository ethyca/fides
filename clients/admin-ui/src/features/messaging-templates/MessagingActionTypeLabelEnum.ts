import { MessagingActionType } from "~/types/api";

const MessagingActionTypeLabelEnum: Record<MessagingActionType, string> = {
  [MessagingActionType.CONSENT_REQUEST]: "Consent Request",
  [MessagingActionType.SUBJECT_IDENTITY_VERIFICATION]:
    "Subject Identity Verification",
  [MessagingActionType.CONSENT_REQUEST_EMAIL_FULFILLMENT]:
    "Consent Request Email Fulfillment",
  [MessagingActionType.MESSAGE_ERASURE_FULFILLMENT]:
    "Message Erasure Fulfillment",
  [MessagingActionType.PRIVACY_REQUEST_ERROR_NOTIFICATION]:
    "Privacy Request Error Notification",
  [MessagingActionType.PRIVACY_REQUEST_RECEIPT]: "Privacy Request Receipt",
  [MessagingActionType.PRIVACY_REQUEST_COMPLETE_ACCESS]:
    "Privacy Request Complete Access",
  [MessagingActionType.PRIVACY_REQUEST_COMPLETE_DELETION]:
    "Privacy Request Complete Deletion",
  [MessagingActionType.PRIVACY_REQUEST_REVIEW_DENY]:
    "Privacy Request Review Deny",
  [MessagingActionType.PRIVACY_REQUEST_REVIEW_APPROVE]:
    "Privacy Request Review Approve",
  [MessagingActionType.TEST_MESSAGE]: "Test Message",
};
export default MessagingActionTypeLabelEnum;
