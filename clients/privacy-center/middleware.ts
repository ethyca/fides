import { NextResponse } from "next/server";
import type { NextRequest} from "next/server";

export default function middleware(request: NextRequest) {
  const start = Date.now();
  const response = NextResponse.next();
  const stop = Date.now();
  const handler_time = stop - start;

  const log_dict = {
    method: request.method,
    status_code: response.status,
    handler_time: `${handler_time}ms`,
    path: request.nextUrl.pathname,
  };
  console.info(JSON.stringify(log_dict));
  return response;
}
