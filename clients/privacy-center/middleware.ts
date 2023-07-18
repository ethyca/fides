import { NextResponse } from 'next/server'

export default function middleware(request) {
  const response = NextResponse.next()
  console.log(request);
  console.log(response);
  return response;
}
