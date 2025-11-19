import { NextRequest, NextResponse } from "next/server";

import { PrivacyCenterSettings } from "./PrivacyCenterSettings";
import {
  MiddlewareResponseInit,
  NodeEnv,
  SecurityHeaderService,
} from "./securityHeadersService";

export const CONTENT_SECURITY_POLICY_HEADER = "Content-Security-Policy";

export type SecurityHeaderPrivacyCenterSettings = Pick<
  PrivacyCenterSettings,
  "FIDES_API_URL" | "GEOLOCATION_API_URL"
>;

function checkIncludedPath(pathname: string) {
  const includePaths = /\/((?!api|_next\/static|_next\/image|favicon\.ico).*)/;
  const matchedContent = includePaths.exec(pathname);
  const isIncludedPath =
    ((matchedContent ?? [])[0]?.length ?? 0) === pathname.length;
  return isIncludedPath;
}

function safelyGetHost(urlString: string = "") {
  if (urlString.length > 0) {
    try {
      return new URL(urlString).host;
    } catch (ex) {
      return "";
    }
  }

  return "";
}

export function getCspHeader(
  nonce: string,
  isDev: boolean,
  {
    fidesApiHost,
    geolocationApiHost,
  }: { fidesApiHost: string; geolocationApiHost: string },
) {
  const cspHeader = `
    default-src 'self';
    script-src 'self' 'nonce-${nonce}' 'strict-dynamic' ${isDev ? "'unsafe-eval'" : ""};
    style-src 'self' ${isDev ? "'unsafe-inline'" : `'nonce-${nonce}'`};
    connect-src 'self' ${fidesApiHost} ${geolocationApiHost};
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

export class RecommendedSecurityHeaderService implements SecurityHeaderService {
  readonly settings: SecurityHeaderPrivacyCenterSettings;

  readonly nodeEnv: NodeEnv;

  readonly randomUUID: () => string;

  constructor(
    nodeEnv: NodeEnv,
    settings: SecurityHeaderPrivacyCenterSettings,
    randomUUID: () => string,
  ) {
    this.settings = settings;
    this.nodeEnv = nodeEnv;
    this.randomUUID = randomUUID;
  }

  applyRequestContext(requestContext: MiddlewareResponseInit): void {
    const nonce = Buffer.from(this.randomUUID()).toString("base64");
    const isDev = this.nodeEnv === "development";
    const fidesApiHost = safelyGetHost(this.settings.FIDES_API_URL);
    const geolocationApiHost = safelyGetHost(this.settings.GEOLOCATION_API_URL);
    const contentSecurityPolicyHeaderValue = getCspHeader(nonce, isDev, {
      fidesApiHost,
      geolocationApiHost,
    });

    requestContext.request.headers.set("x-nonce", nonce);
    requestContext.request.headers.set(
      CONTENT_SECURITY_POLICY_HEADER,
      contentSecurityPolicyHeaderValue,
    );
  }

  // eslint-disable-next-line class-methods-use-this
  applyResponseHeaders(
    middlewareResponse: MiddlewareResponseInit,
    request: NextRequest,
    response: NextResponse,
  ): void {
    response.headers.set("X-Frame-Options", "deny");
    response.headers.set("X-Content-Type-Options", "nosniff");
    response.headers.set(
      "Cache-Control",
      "no-cache, no-store, must-revalidate",
    );
    response.headers.set("Strict-Transport-Security", "max-age=3153600");

    const consentSecurityPolicy = middlewareResponse.request.headers.get(
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
