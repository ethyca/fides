import { NextResponse } from 'next/server'

export default function middleware(request) {
  const start = Date.now()
  const response = NextResponse.next();
  const stop = Date.now()
  const handler_time = stop - start

  const log_dict = { method: request.method, status_code: response.status, handler_time: handler_time.getMilliseconds, path: request.destination }
  console.info(log_dict);
  return response;
}
