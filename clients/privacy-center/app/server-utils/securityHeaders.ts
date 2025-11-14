import { NextRequest, NextResponse } from "next/server";

import { PrivacyCenterSettings } from "./PrivacyCenterSettings";

const CONTENT_SECURITY_POLICY_HEADER = "Content-Security-Policy";

function getCspHeader(
  nonce: string,
  isDev: boolean,
  settings: PrivacyCenterSettings,
) {
  let fidesApiUrlHost = "";
  let fidesGeolocationApiUrlHost = "";

  if (settings.FIDES_API_URL.length > 0) {
    try {
      fidesApiUrlHost = new URL(settings.FIDES_API_URL).host;
    } catch (ex) {
      // log error
    }
  }

  if (settings.GEOLOCATION_API_URL.length > 0) {
    try {
      fidesGeolocationApiUrlHost = new URL(settings.GEOLOCATION_API_URL).host;
    } catch (ex) {
      // log error
    }
  }

  const cspHeader = `
    default-src 'self';
    script-src 'self' 'nonce-${nonce}' 'strict-dynamic' ${isDev ? "'unsafe-eval'" : ""};
    style-src 'self' ${isDev ? "'unsafe-inline'" : `'nonce-${nonce}'`};
    connect-src 'self' ${fidesApiUrlHost} ${fidesGeolocationApiUrlHost};
    img-src 'self' blob: data:;
    font-src 'self';
    object-src 'none';
    base-uri 'self';
    form-action 'self';
    frame-ancestors 'none';
    upgrade-insecure-requests;
`;

  const contentSecurityPolicyHeaderValue = cspHeader
    .replace(/\s{2,}/g, " ")
    .trim();

  return contentSecurityPolicyHeaderValue;
}

export function configureSecurityHeaderContext(
  settings: PrivacyCenterSettings,
  internalResponseHeaders: Headers,
) {
  if (settings.SECURITY_HEADERS_MODE) {
    const isDev = process.env.NODE_ENV === "development";
    const nonce = Buffer.from(crypto.randomUUID()).toString("base64");
    const contentSecurityPolicyHeaderValue = getCspHeader(
      nonce,
      isDev,
      settings,
    );

    internalResponseHeaders.set("x-nonce", nonce);
    internalResponseHeaders.set(
      CONTENT_SECURITY_POLICY_HEADER,
      contentSecurityPolicyHeaderValue,
    );
  }
}

export function configureResponseSecurityHeaders(
  settings: PrivacyCenterSettings,
  request: NextRequest,
  response: NextResponse<unknown>,
  internalResponseHeaders: Headers,
) {
  if (settings.SECURITY_HEADERS_MODE) {
    // Recommended matcher: https://nextjs.org/docs/15/pages/guides/content-security-policy#adding-a-nonce-with-middleware
    const includePaths = /\/((?!api|_next\/static|_next\/image|favicon.ico).*)/;
    const isIncludedPath = includePaths.test(request.nextUrl.pathname);

    response.headers.set("x-Frame-Options", "deny");
    response.headers.set("X-Content-Type-Options", "nosniff");
    response.headers.set(
      "Cache-Control",
      "no-cache, no-store, must-revalidate",
    );
    response.headers.set("Strict-Transport-Security", "max-age=3153600");
    const consentSecurityPolicy = internalResponseHeaders.get(
      CONTENT_SECURITY_POLICY_HEADER,
    );

    if (isIncludedPath && consentSecurityPolicy) {
      response.headers.set(
        CONTENT_SECURITY_POLICY_HEADER,
        consentSecurityPolicy,
      );
    }
  }
}
