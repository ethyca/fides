import { NextRequest } from "next/server";

export default function middleware(request: NextRequest) {
  const logDict = {
    method: request.method,
    path: request.nextUrl.pathname,
  };

  const debug = process.env.FIDES_PRIVACY_CENTER__DEBUG === "true";
  if (debug) {
    /* eslint-disable no-console */
    console.info(JSON.stringify(logDict));
  }
}
