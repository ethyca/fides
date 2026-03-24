export const API_URL = Cypress.env("API_URL");
export const TCF_VERSION_HASH = "q34r3qr4";
export const TEST_OVERRIDE_WINDOW_PATH = "window.config.overrides";

// URL-safe base64 encoded policy keys used in test URLs.
// These correspond to encodePolicyKey() in common/policy-key.ts.
export const ENCODED_ACCESS_POLICY = "MDpkZWZhdWx0X2FjY2Vzc19wb2xpY3k"; // 0:default_access_policy
export const ENCODED_ERASURE_POLICY = "MTpkZWZhdWx0X2VyYXN1cmVfcG9saWN5"; // 1:default_erasure_policy
