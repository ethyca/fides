/* istanbul ignore file */
import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export default function middleware(request: NextRequest) {
  const start = Date.now();
  const response = NextResponse.next();
  const stop = Date.now();
  const handlerTime = stop - start;

  const logDict = {
    method: request.method,
    status_code: response.status,
    handler_time: `${handlerTime}ms`,
    path: request.nextUrl.pathname,
  };

  /* eslint-disable no-console */
  console.info(JSON.stringify(logDict));
  /* eslint-enable no-console */
  return response;
}
