export const API_URL = Cypress.env("API_URL");
export const TCF_VERSION_HASH = "q34r3qr4";
export const TEST_OVERRIDE_WINDOW_PATH = "window.config.overrides";

// URL-safe base64 encoded policy keys used in test URLs.
// These correspond to encodePolicyKey() in common/policy-key.ts.
export const ENCODED_ACCESS_POLICY = "ZGVmYXVsdF9hY2Nlc3NfcG9saWN5"; // default_access_policy
export const ENCODED_ERASURE_POLICY = "ZGVmYXVsdF9lcmFzdXJlX3BvbGljeQ"; // default_erasure_policy
