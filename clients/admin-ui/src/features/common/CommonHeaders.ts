/**
 * Adds common headers to all api calls to fidesops
 */
export function addCommonHeaders(headers: Headers, token: string | null) {
  headers.set("Access-Control-Allow-Origin", "*");
  headers.set("X-Fides-Source", "fidesops-admin-ui");
  if (token) {
    headers.set("authorization", `Bearer ${token}`);
  }
  headers.set("Unescape-Safestr", "true");
  return headers;
}
