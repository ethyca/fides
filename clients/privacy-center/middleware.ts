import { NextRequest, NextResponse } from "next/server";
import { v4 } from "uuid";

import loadEnvironmentVariables from "./app/server-utils/loadEnvironmentVariables";
import { createLogger } from "./app/server-utils/logger";
import { NullSecurityHeaderService } from "./app/server-utils/nullSecurityHeaderService";
import { RecommendedSecurityHeaderService } from "./app/server-utils/recommendedSecurityHeaderService";
import {
  MiddlewareResponseInit,
  SecurityHeaderService,
} from "./app/server-utils/securityHeadersService";

export default function middleware(request: NextRequest) {
  const settings = loadEnvironmentVariables();
  const log = createLogger();
  const requestId = v4();
  const securityHeadersService: SecurityHeaderService =
    settings.SECURITY_HEADERS_MODE === "recommended"
      ? new RecommendedSecurityHeaderService(
          process.env.NODE_ENV,
          settings,
          crypto.randomUUID,
        )
      : new NullSecurityHeaderService();

  const logDict = {
    method: request.method,
    path: request.nextUrl.pathname,
    requestId,
  };

  log.debug(logDict, "Request received");

  // internalResponseHeaders are used to pass data between different contexts in NextJS.
  // These headers will not appear on the actual response headers on a network call.
  const middlewareResponseHeaders = new Headers(request.headers);
  middlewareResponseHeaders.set("x-request-id", requestId);
  const middlewareResponse: MiddlewareResponseInit = {
    request: {
      headers: middlewareResponseHeaders,
    },
  };

  securityHeadersService.applyRequestContext(middlewareResponse);

  const response = NextResponse.next(middlewareResponse);

  securityHeadersService.applyResponseHeaders(
    middlewareResponse,
    request,
    response,
  );

  return response;
}
