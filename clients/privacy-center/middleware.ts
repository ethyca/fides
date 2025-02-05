import { NextRequest, NextResponse } from "next/server";

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

  /*
    Set the query params as a header for the response
    This is a workaround to pass the query params to server layout.tsx
    src: https://github.com/vercel/next.js/discussions/54955#discussioncomment-11744585
  */
  const response = NextResponse.next();
  const searchParams = request.nextUrl.searchParams.toString();
  response.headers.set("searchParams", searchParams);

  return response;
}
