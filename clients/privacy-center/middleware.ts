import { NextRequest, NextResponse } from "next/server";
import { v4 } from "uuid";

import loadEnvironmentVariables from "./app/server-utils/loadEnvironmentVariables";
import { createLogger } from "./app/server-utils/logger";
import {
  configureResponseSecurityHeaders,
  configureSecurityHeaderContext,
} from "./app/server-utils/securityHeaders";

export default function middleware(request: NextRequest) {
  const settings = loadEnvironmentVariables();
  const log = createLogger();
  const requestId = v4();

  const logDict = {
    method: request.method,
    path: request.nextUrl.pathname,
    requestId,
  };

  log.debug(logDict, "Request received");

  // internalResponseHeaders are used to pass data between different contexts in NextJS.
  // These headers will not appear on the actual response headers on a network call.
  const internalResponseHeaders = new Headers(request.headers);
  internalResponseHeaders.set("x-request-id", requestId);

  configureSecurityHeaderContext(settings, internalResponseHeaders);

  const response = NextResponse.next({
    request: {
      headers: internalResponseHeaders,
    },
  });

  configureResponseSecurityHeaders({
    request,
    response,
    internalResponseHeaders,
    settings,
  });

  return response;
}
