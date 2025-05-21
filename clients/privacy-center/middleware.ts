import { NextRequest, NextResponse } from "next/server";
import { v4 } from "uuid";

import loadEnvironmentVariables from "./app/server-utils/loadEnvironmentVariables";
import { createLogger } from "./app/server-utils/logger";

export default function middleware(request: NextRequest) {
  const envVars = loadEnvironmentVariables();
  const log = createLogger({
    logLevel: envVars.LOG_LEVEL,
  });
  const requestId = v4();

  const logDict = {
    method: request.method,
    path: request.nextUrl.pathname,
    requestId,
  };

  log.debug(logDict);

  const requestHeaders = new Headers(request.headers);
  requestHeaders.set("x-request-id", requestId);
  const response = NextResponse.next({
    request: {
      headers: requestHeaders,
    },
  });

  return response;
}
