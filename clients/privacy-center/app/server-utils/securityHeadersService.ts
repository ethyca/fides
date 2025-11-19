import { NextRequest, NextResponse } from "next/server";

export type NodeEnv = typeof process.env.NODE_ENV;

export interface MiddlewareResponseInit {
  request: { headers: Headers };
}

export interface SecurityHeaderService {
  applyRequestContext(middlewareResponseInit: MiddlewareResponseInit): void;
  applyResponseHeaders(
    middlewareResponse: MiddlewareResponseInit,
    request: NextRequest,
    response: NextResponse,
  ): void;
}
