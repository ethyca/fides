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

export const SubjectRequestStatusOptions = [...SubjectRequestStatusMap].map(
  ([key, value]) => ({
    label: value,
    value: key,
  }),
);

export const SubjectRequestActionTypeMap = new Map<ActionType, string>([
  [ActionType.ACCESS, "Access"],
  [ActionType.ERASURE, "Erasure"],
  [ActionType.CONSENT, "Consent"],
  [ActionType.UPDATE, "Update"],
]);

export const SubjectRequestActionTypeOptions = [
  ...SubjectRequestActionTypeMap,
].map(([key, value]) => ({
  label: value,
  value: key,
}));

export const messagingProviders = {
  mailgun: "mailgun",
  twilio_email: "twilio_email",
  twilio_text: "twilio_text",
};

export const storageTypes = {
  local: "local",
  s3: "s3",
};
