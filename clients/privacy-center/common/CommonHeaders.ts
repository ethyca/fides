import { Headers as HeadersPolyfill } from "headers-polyfill";

/**
 * Adds common headers to all api calls to fides
 * TypeScript 5 Note: We use a union type to support both native Headers and headers-polyfill
 */
export function addCommonHeaders(
  headers: Headers | HeadersPolyfill,
  token?: string | null,
): Headers {
  headers.set("Access-Control-Allow-Origin", "*");
  headers.set("X-Fides-Source", "fides-privacy-center");
  headers.set("Accept", "application/json");
  if (!headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  if (token) {
    headers.set("authorization", `Bearer ${token}`);
  }
  headers.set("Unescape-Safestr", "true");
  return headers as Headers;
}
