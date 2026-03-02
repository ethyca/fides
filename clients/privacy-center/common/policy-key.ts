/**
 * Encode a policy key for use in a URL path segment using URL-safe base64.
 * Standard base64 uses +, /, and = which require percent-encoding in URLs,
 * so we substitute: + -> -, / -> _, and strip padding =.
 */
export const encodePolicyKey = (key: string): string =>
  btoa(key).replace(/\+/g, "-").replace(/\//g, "_").replace(/=/g, "");

/**
 * Decode a URL-safe base64-encoded policy key from a URL path segment.
 */
export const decodePolicyKey = (encoded: string): string =>
  atob(encoded.replace(/-/g, "+").replace(/_/g, "/"));
