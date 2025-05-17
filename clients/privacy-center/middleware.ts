import { NextRequest, NextResponse } from "next/server";
import { v4 } from "uuid";

export default function middleware(request: NextRequest) {
  const requestId = v4();

  const logDict = {
    method: request.method,
    path: request.nextUrl.pathname,
    requestId,
  };

  const debug = process.env.FIDES_PRIVACY_CENTER__DEBUG === "true";
  if (debug) {
    /* eslint-disable no-console */
    console.info(JSON.stringify(logDict));
  }

  const requestHeaders = new Headers(request.headers);
  requestHeaders.set("x-request-id", requestId);
  const response = NextResponse.next({
    request: {
      headers: requestHeaders,
    },
  });

  return response;
}
