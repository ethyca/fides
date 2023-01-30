/**
 * Adds common headers to all api calls to fides
 */
export function addCommonHeaders(headers: Headers, token?: string | null) {
  headers.set("Access-Control-Allow-Origin", "*");
  headers.set("X-Fides-Source", "fides-privacy-center");
  headers.set("Accept", "application/json");
  headers.set("Content-Type", "application/json");
  if (token) {
    headers.set("authorization", `Bearer ${token}`);
  }
  return headers;
}
