import { NextRequest, NextResponse } from "next/server";
import { v4 } from "uuid";

import {
  applyRequestContext,
  applyResponseHeaders,
  getApplicableHeaderRules,
  MiddlewareResponseInit,
} from "./app/server-utils/headers";
import loadEnvironmentVariables from "./app/server-utils/loadEnvironmentVariables";
import { createLogger } from "./app/server-utils/logger";
import { PrivacyCenterSettings } from "./app/server-utils/PrivacyCenterSettings";
import { recommendedSecurityHeaders } from "./app/server-utils/recommendedSecurityHeaders";
import { safelyGetHost } from "./app/server-utils/safelyGetHost";

let cachedSettings: boolean = false;
let settings: PrivacyCenterSettings;
let isDev: boolean;
let fidesApiHost: string;
let geolocationApiHost: string;

export default function middleware(request: NextRequest) {
  const log = createLogger();
  const requestId = v4();

  const logDict = {
    method: request.method,
    path: request.nextUrl.pathname,
    requestId,
  };

  log.debug(logDict, "Request received");

  const requestHeaders = new Headers(request.headers);
  requestHeaders.set("x-request-id", requestId);

  if (!cachedSettings) {
    settings = loadEnvironmentVariables();
    isDev = process.env.NODE_ENV === "development";
    fidesApiHost = safelyGetHost(settings.FIDES_API_URL);
    geolocationApiHost = safelyGetHost(settings.GEOLOCATION_API_URL);
    cachedSettings = true;
  }

  const headerRules =
    settings.SECURITY_HEADERS_MODE === "recommended"
      ? recommendedSecurityHeaders(isDev, fidesApiHost, geolocationApiHost)
      : [];

  const { contextAppliers, headerDefinitions } = getApplicableHeaderRules(
    request.nextUrl.pathname,
    headerRules,
  );

  const initializer: MiddlewareResponseInit = {
    request: {
      headers: requestHeaders,
    },
  };

  applyRequestContext(contextAppliers, initializer);

  const response = NextResponse.next(initializer);

  applyResponseHeaders(initializer, headerDefinitions, response);

  return response;
}
