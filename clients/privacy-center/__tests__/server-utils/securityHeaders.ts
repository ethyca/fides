import { NextRequest, NextResponse } from "next/server";

import {
  configureResponseSecurityHeaders,
  CONTENT_SECURITY_POLICY_HEADER,
} from "~/app/server-utils/securityHeaders";

const mockRequestFactory = jest.fn(
  (pathname: string) =>
    ({
      nextUrl: { pathname },
    }) as NextRequest,
);

const API_PATH = "/api/v1/example";
const STATIC_ASSET_PATH = "/_next/static";
const PAGE_PATH = "/example";

function expectHeadersThatArePresentOnEveryRequest(headers: Headers) {
  expect(headers.get("cache-control")).toBe(
    "no-cache, no-store, must-revalidate",
  );
  expect(headers.get("strict-transport-security")).toBe("max-age=3153600");
  expect(headers.get("x-content-type-options")).toBe("nosniff");
  expect(headers.get("x-frame-options")).toBe("deny");
  expect(headers.get("x-middleware-next")).toBe("1");
}

describe("securityHeaders", () => {
  beforeEach(() => {
    mockRequestFactory.mockClear();
  });

  describe("configureResponseSecurityHeaders", () => {
    it("does not set security headers when the feature is off", () => {
      const headers = new Headers();

      const mockResponse = NextResponse.next();
      const mockRequest = mockRequestFactory("/irrelevant-path");
      configureResponseSecurityHeaders({
        settings: {
          SECURITY_HEADERS_MODE: "none",
        },
        internalResponseHeaders: headers,
        request: mockRequest,
        response: mockResponse,
      });

      expect(mockResponse.headers.entries).toHaveLength(0);
    });

    it.each([API_PATH, PAGE_PATH, STATIC_ASSET_PATH])(
      "has standard security headers when the feature is on for every path type",
      (path) => {
        const mockHeaders = new Headers();
        const mockResponse = NextResponse.next();
        const mockRequest = mockRequestFactory(path);
        configureResponseSecurityHeaders({
          settings: {
            SECURITY_HEADERS_MODE: "recommended",
          },
          internalResponseHeaders: mockHeaders,
          request: mockRequest,
          response: mockResponse,
        });

        const { headers } = mockResponse;
        expectHeadersThatArePresentOnEveryRequest(headers);
      },
    );

    it.each([API_PATH, PAGE_PATH, STATIC_ASSET_PATH])(
      "has standard security headers when the feature is on for every path type",
      (path) => {
        const mockHeaders = new Headers();
        const mockResponse = NextResponse.next();
        const mockRequest = mockRequestFactory(path);
        configureResponseSecurityHeaders({
          settings: {
            SECURITY_HEADERS_MODE: "recommended",
          },
          internalResponseHeaders: mockHeaders,
          request: mockRequest,
          response: mockResponse,
        });

        const { headers } = mockResponse;
        expectHeadersThatArePresentOnEveryRequest(headers);
      },
    );

    it("has CSP header set for page-like paths", () => {
      const mockHeaders = new Headers();
      const mockCspHeaderValue = "example-value";
      mockHeaders.set(CONTENT_SECURITY_POLICY_HEADER, mockCspHeaderValue);
      const mockResponse = NextResponse.next();
      const mockRequest = mockRequestFactory(PAGE_PATH);
      configureResponseSecurityHeaders({
        settings: {
          SECURITY_HEADERS_MODE: "recommended",
        },
        internalResponseHeaders: mockHeaders,
        request: mockRequest,
        response: mockResponse,
      });

      const { headers } = mockResponse;
      expect(headers.get(CONTENT_SECURITY_POLICY_HEADER)).toBe(
        mockCspHeaderValue,
      );
    });

    it.each([API_PATH, STATIC_ASSET_PATH])(
      "does not have CSP header set for non-page-like path",
      (path) => {
        const mockHeaders = new Headers();
        const mockCspHeaderValue = "example-value";
        mockHeaders.set(CONTENT_SECURITY_POLICY_HEADER, mockCspHeaderValue);
        const mockResponse = NextResponse.next();
        const mockRequest = mockRequestFactory(path);
        configureResponseSecurityHeaders({
          settings: {
            SECURITY_HEADERS_MODE: "recommended",
          },
          internalResponseHeaders: mockHeaders,
          request: mockRequest,
          response: mockResponse,
        });

        const { headers } = mockResponse;
        expect(headers.get(CONTENT_SECURITY_POLICY_HEADER)).toBeFalsy();
      },
    );
  });
});
