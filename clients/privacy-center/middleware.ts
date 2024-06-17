import type { NextRequest } from "next/server";

export default function middleware(request: NextRequest) {
  const logDict = {
    method: request.method,
    path: request.nextUrl.pathname,
  };

  /* eslint-disable no-console */
  console.info(JSON.stringify(logDict));
}
