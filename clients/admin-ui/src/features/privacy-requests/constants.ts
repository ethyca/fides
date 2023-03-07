/**
 * Subject request status key/value pairs
 */
export const SubjectRequestStatusMap = new Map<string, string>([
  ["Approved", "approved"],
  ["Canceled", "canceled"],
  ["Completed", "complete"],
  ["Denied", "denied"],
  ["Error", "error"],
  ["In Progress", "in_processing"],
  ["New", "pending"],
  ["Paused", "paused"],
  ["Unverified", "identity_unverified"],
  ["Requires input", "requires_input"],
]);

export const messagingProviders = {
  mailgun: "MAILGUN",
  twilio_email: "TWILIO_EMAIL",
  twilio_text: "TWILIO_TEXT",
};

export const storageTypes = {
  local: "local",
  s3: "s3",
};
