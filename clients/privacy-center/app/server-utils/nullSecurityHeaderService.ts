import { NextRequest, NextResponse } from "next/server";

import {
  MiddlewareResponseInit,
  SecurityHeaderService,
} from "./securityHeadersService";

export class NullSecurityHeaderService implements SecurityHeaderService {
  // eslint-disable-next-line class-methods-use-this, @typescript-eslint/no-unused-vars
  applyRequestContext(_requestContext: MiddlewareResponseInit): void {
    // No-op
  }

  // eslint-disable-next-line class-methods-use-this
  applyResponseHeaders(
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    _middlewareResponse: MiddlewareResponseInit,
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    _request: NextRequest,
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    _response: NextResponse,
  ): void {}
}
