import { ActionType, PrivacyRequestStatus } from "~/types/api";

export const SubjectRequestStatusMap = new Map<PrivacyRequestStatus, string>([
  [PrivacyRequestStatus.APPROVED, "Approved"],
  [PrivacyRequestStatus.CANCELED, "Canceled"],
  [PrivacyRequestStatus.COMPLETE, "Completed"],
  [PrivacyRequestStatus.DENIED, "Denied"],
  [PrivacyRequestStatus.ERROR, "Error"],
  [PrivacyRequestStatus.IN_PROCESSING, "In Progress"],
  [PrivacyRequestStatus.PENDING, "New"],
  [PrivacyRequestStatus.PAUSED, "Paused"],
  [PrivacyRequestStatus.IDENTITY_UNVERIFIED, "Unverified"],
  [PrivacyRequestStatus.REQUIRES_INPUT, "Requires input"],
]);

export const SubjectRequestActionTypeMap = new Map<ActionType, string>([
  [ActionType.ACCESS, "Access"],
  [ActionType.ERASURE, "Erasure"],
  [ActionType.CONSENT, "Consent"],
  [ActionType.UPDATE, "Update"],
]);

export const storageTypes = {
  local: "local",
  s3: "s3",
};
