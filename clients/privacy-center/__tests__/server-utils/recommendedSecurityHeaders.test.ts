import { NextRequest, NextResponse } from "next/server";

import { NullSecurityHeaderService } from "~/app/server-utils/nullSecurityHeaderService";
import {
  CONTENT_SECURITY_POLICY_HEADER,
  RecommendedSecurityHeaderService,
  SecurityHeaderPrivacyCenterSettings,
} from "~/app/server-utils/recommendedSecurityHeaderService";
import {
  MiddlewareResponseInit,
  NodeEnv,
  SecurityHeaderService,
} from "~/app/server-utils/securityHeadersService";

const API_PATH = "/api/v1/example";
const STATIC_ASSET_PATH = "/_next/static";
const IMAGE_ASSET_PATH = "/_next/static";
const FAVICON_PATH = "favicon.ico";
const PAGE_PATH = "/example";

const DEFAULT_ENV_VARS = {
  FIDES_API_URL: "http://example.com/api/v1",
  GEOLOCATION_API_URL: "http://geolocation.example.com/",
};
const MOCK_UUID = "mock-uuid";
const uuidFactory = jest.fn(() => () => MOCK_UUID);

const recommendedServiceFn = (
  env: NodeEnv = "production",
  settings: SecurityHeaderPrivacyCenterSettings = DEFAULT_ENV_VARS,
  randomUUID: () => string = uuidFactory(),
) => new RecommendedSecurityHeaderService(env, settings, randomUUID);

const serviceFactory = jest.fn<
  SecurityHeaderService,
  Parameters<typeof recommendedServiceFn>,
  any
>(recommendedServiceFn);

const mockRequestFactory = jest.fn<NextRequest, [], any>();

describe(RecommendedSecurityHeaderService, () => {
  beforeEach(() => {
    serviceFactory.mockClear();
  });

  describe.each([
    { pathname: API_PATH, withCsp: false },
    { pathname: STATIC_ASSET_PATH, withCsp: false },
    { pathname: IMAGE_ASSET_PATH, withCsp: false },
    { pathname: FAVICON_PATH, withCsp: false },
    { pathname: PAGE_PATH, withCsp: true },
  ])(
    "adds standard security headers when the feature is on for a path like $pathname",
    ({ pathname, withCsp }) => {
      let fakeResponse: NextResponse;
      const mockCspHeader = "mock-response-csp-header";

      beforeEach(() => {
        const service = serviceFactory();
        const middlewareResponseInit: MiddlewareResponseInit = {
          request: { headers: new Headers() },
        };

        middlewareResponseInit.request.headers.set(
          CONTENT_SECURITY_POLICY_HEADER,
          mockCspHeader,
        );
        mockRequestFactory.mockImplementation(
          () => ({ nextUrl: { pathname } }) as NextRequest,
        );
        const mockRequest = mockRequestFactory();

        fakeResponse = NextResponse.next(middlewareResponseInit);
        service.applyResponseHeaders(
          middlewareResponseInit,
          mockRequest,
          fakeResponse,
        );
      });

      test("that standard response headers are set", () => {
        expect(fakeResponse.headers.get("cache-control")).toBe(
          "no-cache, no-store, must-revalidate",
        );
        expect(fakeResponse.headers.get("strict-transport-security")).toBe(
          "max-age=3153600",
        );
        expect(fakeResponse.headers.get("x-content-type-options")).toBe(
          "nosniff",
        );
        expect(fakeResponse.headers.get("x-frame-options")).toBe("deny");
        expect(fakeResponse.headers.get("x-middleware-next")).toBe("1");
        expect(fakeResponse.headers.get("x-middleware-override-headers")).toBe(
          "content-security-policy",
        );
        expect(
          fakeResponse.headers.get(
            "x-middleware-request-content-security-policy",
          ),
        ).toBe("mock-response-csp-header");
        if (withCsp) {
          expect(fakeResponse.headers.get(CONTENT_SECURITY_POLICY_HEADER)).toBe(
            mockCspHeader,
          );
        } else {
          expect(
            fakeResponse.headers.get(CONTENT_SECURITY_POLICY_HEADER),
          ).toBeFalsy();
        }
      });
    },
  );

  test.each([
    {
      description: "dev mode has unsafe eval and unsafe inline",
      env: "development",
      cspHeader:
        "default-src 'self'; script-src 'self' 'nonce-bW9jay11dWlk' 'strict-dynamic' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; connect-src 'self' example.com geolocation.example.com; img-src 'self' blob: data:; font-src 'self'; object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'; upgrade-insecure-requests;",
    },
    {
      description: "prod does not have unsafe eval or unsafe inline",
      env: "production",
      cspHeader:
        "default-src 'self'; script-src 'self' 'nonce-bW9jay11dWlk' 'strict-dynamic' ; style-src 'self' 'nonce-bW9jay11dWlk'; connect-src 'self' example.com geolocation.example.com; img-src 'self' blob: data:; font-src 'self'; object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'; upgrade-insecure-requests;",
    },
    {
      description: "that the api urls can be changed",
      env: "production",
      cspHeader:
        "default-src 'self'; script-src 'self' 'nonce-bW9jay11dWlk' 'strict-dynamic' ; style-src 'self' 'nonce-bW9jay11dWlk'; connect-src 'self' fides.example.com geolocation2.example.com; img-src 'self' blob: data:; font-src 'self'; object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'; upgrade-insecure-requests;",
      fidesApiUrl: "https://fides.example.com",
      geolocationApiUrl: "https://geolocation2.example.com",
    },
  ] as {
    description: string;
    env: NodeEnv;
    cspHeader: string;
    fidesApiUrl?: string;
    geolocationApiUrl?: string;
  }[])(
    "that request context can be created and that $.description",
    ({ env, cspHeader, fidesApiUrl, geolocationApiUrl }) => {
      const service = serviceFactory(env, {
        FIDES_API_URL: fidesApiUrl ?? DEFAULT_ENV_VARS.FIDES_API_URL,
        GEOLOCATION_API_URL:
          geolocationApiUrl ?? DEFAULT_ENV_VARS.GEOLOCATION_API_URL,
      });
      const middlewareResponseInit: MiddlewareResponseInit = {
        request: { headers: new Headers() },
      };

      service.applyRequestContext(middlewareResponseInit);

      expect(middlewareResponseInit.request.headers.get("x-nonce")).toBe(
        "bW9jay11dWlk",
      );
      expect(
        middlewareResponseInit.request.headers.get("Content-Security-Policy"),
      ).toBe(cspHeader);
    },
  );
});
