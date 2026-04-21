export const IDP_SESSION_KEYS = {
  ACTION_KEY: "idpActionKey",
  PROVIDER: "idpProvider",
  STATE: "idpState",
  FORM_DATA: "idpFormData",
  BASE_PATH: "idpBasePath",
} as const;

export const IDP_ERROR_MESSAGES = {
  AUTHORIZE_FAILED: "Failed to connect to identity provider",
  CALLBACK_FAILED: "Identity verification failed. Please try again.",
  REQUEST_FAILED: "Failed to submit privacy request",
} as const;
