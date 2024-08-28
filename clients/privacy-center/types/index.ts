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

export enum Layer1ButtonOption {
  // defines the buttons to show in the layer 1 banner
  ACKNOWLEDGE = "acknowledge", // show acknowledge button
  OPT_IN_OPT_OUT = "opt_in_opt_out", // show opt in and opt out buttons
}
