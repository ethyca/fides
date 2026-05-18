import {
  ActionType,
  PrivacyRequestSource,
  PrivacyRequestStatus,
} from "~/types/api";

export const SubjectRequestStatusMap = new Map<PrivacyRequestStatus, string>([
  [PrivacyRequestStatus.APPROVED, "Approved"],
  [PrivacyRequestStatus.AWAITING_EMAIL_SEND, "Awaiting email send"],
  [PrivacyRequestStatus.CANCELED, "Canceled"],
  [PrivacyRequestStatus.COMPLETE, "Completed"],
  [PrivacyRequestStatus.DENIED, "Denied"],
  [PrivacyRequestStatus.ERROR, "Error"],
  [PrivacyRequestStatus.IN_PROCESSING, "In progress"],
  [PrivacyRequestStatus.PENDING, "New"],
  [PrivacyRequestStatus.PAUSED, "Paused"],
  [PrivacyRequestStatus.IDENTITY_UNVERIFIED, "Unverified"],
  [PrivacyRequestStatus.REQUIRES_INPUT, "Requires input"],
  [PrivacyRequestStatus.REQUIRES_MANUAL_FINALIZATION, "Requires finalization"],
  [PrivacyRequestStatus.DUPLICATE, "Duplicate"],
  [PrivacyRequestStatus.AWAITING_PRE_APPROVAL, "Awaiting external review"],
  [PrivacyRequestStatus.PRE_APPROVAL_NOT_ELIGIBLE, "Manual review required"],
  [PrivacyRequestStatus.PENDING_EXTERNAL, "Pending external"],
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

// Dataset Test is intentionally omitted — those are system-internal test runs,
// not user-facing DSRs, and should not be filterable from the Request Manager UI.
// The backend still accepts the Dataset Test source for programmatic API use.
export const SubjectRequestSourceMap = new Map<PrivacyRequestSource, string>([
  [PrivacyRequestSource.PRIVACY_CENTER, "Privacy Center"],
  [PrivacyRequestSource.REQUEST_MANAGER, "Request Manager"],
  [PrivacyRequestSource.CONSENT_WEBHOOK, "Consent Webhook"],
  [PrivacyRequestSource.FIDES_JS, "Fides.js"],
  [PrivacyRequestSource.JANUS_SDK, "Mobile SDK"],
]);

export const SubjectRequestSourceOptions = [...SubjectRequestSourceMap].map(
  ([key, value]) => ({
    label: value,
    value: key,
  }),
);

export const messagingProviders = {
  mailgun: "mailgun",
  twilio_email: "twilio_email",
  twilio_text: "twilio_text",
};

export const storageTypes = {
  local: "local",
  s3: "s3",
  gcs: "gcs",
};
