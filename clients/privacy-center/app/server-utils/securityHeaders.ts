import { NextRequest, NextResponse } from "next/server";

import { PrivacyCenterSettings } from "./PrivacyCenterSettings";

export const CONTENT_SECURITY_POLICY_HEADER = "Content-Security-Policy";

type CspPrivacyCenterSettings = Pick<
  PrivacyCenterSettings,
  "FIDES_API_URL" | "GEOLOCATION_API_URL"
>;

type SecurityHeaderPrivacyCenterSettings = Pick<
  PrivacyCenterSettings,
  "SECURITY_HEADERS_MODE"
>;

function getCspHeader(
  nonce: string,
  isDev: boolean,
  settings: CspPrivacyCenterSettings,
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
  settings: CspPrivacyCenterSettings & SecurityHeaderPrivacyCenterSettings,
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

function checkIncludedPath(pathname: string) {
  const includePaths = /\/((?!api|_next\/static|_next\/image|favicon\.ico).*)/;
  const matchedContent = includePaths.exec(pathname);
  const isIncludedPath =
    ((matchedContent ?? [])[0]?.length ?? 0) === pathname.length;
  return isIncludedPath;
}

export function configureResponseSecurityHeaders({
  settings,
  request,
  response,
  internalResponseHeaders,
}: {
  settings: Pick<PrivacyCenterSettings, "SECURITY_HEADERS_MODE">;
  request: NextRequest;
  response: NextResponse<unknown>;
  internalResponseHeaders: Headers;
}) {
  if (settings.SECURITY_HEADERS_MODE === "recommended") {
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

    // Recommended matcher: https://nextjs.org/docs/15/pages/guides/content-security-policy#adding-a-nonce-with-middleware
    const { pathname } = request.nextUrl;
    const isIncludedPath = checkIncludedPath(pathname);
    if (isIncludedPath && consentSecurityPolicy) {
      response.headers.set(
        CONTENT_SECURITY_POLICY_HEADER,
        consentSecurityPolicy,
      );
    }
  }
}
