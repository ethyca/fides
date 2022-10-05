/* eslint-disable import/prefer-default-export */

export enum PrivacyRequestStatus {
  APPROVED = "approved",
  COMPLETE = "complete",
  DENIED = "denied",
  ERROR = "error",
  IN_PROCESSING = "in_processing",
  PAUSED = "paused",
  CANCELED = "canceled",
  PENDING = "pending",
  IDENTITY_UNVERIFIED = "identity_unverified",
  REQUIRES_INPUT = "requires_input",
}

export type ConsentItem = {
  fidesDataUseKey: string;
  name: string;
  description: string;
  highlight: boolean;
  url: string;
  defaultValue: boolean;
  // eslint-disable-next-line react/require-default-props
  consentValue?: boolean;
};
