export const IDP_SESSION_KEYS = {
  EMAIL: "idpEmail",
  FIRST_NAME: "idpFirstName",
  LAST_NAME: "idpLastName",
  VERIFICATION_TOKEN: "idpVerificationToken",
  PROVIDER: "idpProvider",
  STATE: "idpState",
  BASE_PATH: "idpBasePath",
} as const;

export const IDP_ERROR_MESSAGES = {
  AUTHORIZE_FAILED: "Failed to connect to identity provider",
  CALLBACK_FAILED: "Identity verification failed. Please try again.",
  REQUEST_FAILED: "Failed to submit privacy request",
} as const;
