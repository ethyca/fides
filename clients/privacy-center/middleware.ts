import { init } from "next/dist/compiled/webpack/webpack";
import { NextRequest, NextResponse } from "next/server";
import { v4 } from "uuid";

import loadEnvironmentVariables from "./app/server-utils/loadEnvironmentVariables";
import { createLogger } from "./app/server-utils/logger";
import { PrivacyCenterSettings } from "./app/server-utils/PrivacyCenterSettings";

export interface MiddlewareResponseInit {
  request: { headers: Headers };
}

function isExactMatch(matcher: RegExp, pathname: string) {
  const matchedContent = matcher.exec(pathname);
  const isIncludedPath =
    ((matchedContent ?? [])[0]?.length ?? 0) === pathname.length;
  return isIncludedPath;
}
type NodeEnv = typeof process.env.NODE_ENV;
type SimpleHeader = [string, string];

interface ContextController {
  hasContext: (name: string) => boolean;
  setContext: (name: string, value: string) => void;
  getContext: (name: string) => string | null;
}

type ContextHandler = (args: ContextController) => void;

interface DynamicHeader {
  name: string;
  context: ContextHandler;
  value: (context: Headers) => string;
}

type HeaderDefinition = SimpleHeader | DynamicHeader;

interface HeaderRule {
  matcher: RegExp;
  headers: HeaderDefinition[];
}

const staticPageCspHeader = (args: {
  fidesApiHost: string;
  geolocationApiHost: string;
}) =>
  `
    default-src 'self';
    script-src 'self' 'unsafe-inline';
    style-src 'self' 'unsafe-inline';
    connect-src 'self' ${args.fidesApiHost} ${args.geolocationApiHost};
    img-src 'self' blob: data:;
    font-src 'self';
    object-src 'none';
    base-uri 'self';
    form-action 'self';
    frame-ancestors 'none';
    upgrade-insecure-requests;
`
    .replace(/\s{2,}/g, " ")
    .trim();

const privacyCenterPagesCspHeader = (args: {
  isDev: boolean;
  fidesApiHost: string;
  geolocationApiHost: string;
  nonce: string;
}) =>
  `
    default-src 'self';
    script-src 'self' 'nonce-${args.nonce}' 'strict-dynamic' ${args.isDev ? "'unsafe-eval'" : ""};
    style-src 'self' ${args.isDev ? "'unsafe-inline'" : `'nonce-${args.nonce}'`};
    connect-src 'self' ${args.fidesApiHost} ${args.geolocationApiHost};
    img-src 'self' blob: data:;
    font-src 'self';
    object-src 'none';
    base-uri 'self';
    form-action 'self';
    frame-ancestors 'none';
    upgrade-insecure-requests;
`
    .replace(/\s{2,}/g, " ")
    .trim();

function getApplicableHeaderRules(pathname: string, headerRules: HeaderRule[]) {
  const matchingRules = headerRules.filter((rule) =>
    isExactMatch(rule.matcher, pathname),
  );

  const headerNames: Set<string> = new Set();
  const headerDefinitions: HeaderDefinition[] = [];
  const contextAppliers: ContextHandler[] = [];

  matchingRules.forEach((rule) =>
    rule.headers.forEach((header) => {
      let headerName: string;
      const dynamicHeader = !Array.isArray(header);
      if (dynamicHeader) {
        headerName = header.name;
        if (header.context) {
          contextAppliers.push(header.context);
        }
      } else {
        [headerName] = header;
      }

      if (!headerNames.has(headerName)) {
        headerNames.add(headerName);
        headerDefinitions.push(header);
      }
    }),
  );

  return { headerDefinitions, contextAppliers };
}

function applyRequestContext(
  contextControllers: ContextHandler[],
  context: MiddlewareResponseInit,
): void {
  const controller: ContextController = {
    getContext: (header) => context.request.headers.get(header),
    hasContext: (header) => context.request.headers.has(header),
    setContext: (header, value) => context.request.headers.set(header, value),
  };
  contextControllers.forEach((applier) => applier(controller));
}

function applyResponseHeaders(
  middlewareResponseInitializer: MiddlewareResponseInit,
  headerDefinitions: HeaderDefinition[],
  response: NextResponse,
): void {
  const context = new Headers(middlewareResponseInitializer.request.headers);
  headerDefinitions.forEach((headerDefinition) => {
    if (Array.isArray(headerDefinition)) {
      response.headers.set(...headerDefinition);
    } else {
      response.headers.set(
        headerDefinition.name,
        headerDefinition.value(context),
      );
    }
  });
}

const CONTENT_SECURITY_POLICY_HEADER = "Content-Security-Policy";

function safelyGetHost(urlString: string = "") {
  if (urlString.length > 0) {
    try {
      return new URL(urlString).host;
    } catch (ex) {
      return "";
    }
  }

  return "";
}

let cachedSettings: boolean = false;
let settings: PrivacyCenterSettings;
let isDev: boolean;
let fidesApiHost: string;
let geolocationApiHost: string;

export default function middleware(request: NextRequest) {
  const log = createLogger();
  const requestId = v4();

  const logDict = {
    method: request.method,
    path: request.nextUrl.pathname,
    requestId,
  };

  log.debug(logDict, "Request received");

  const requestHeaders = new Headers(request.headers);
  requestHeaders.set("x-request-id", requestId);

  if (!cachedSettings) {
    settings = loadEnvironmentVariables();
    isDev = process.env.NODE_ENV === "development";
    fidesApiHost = safelyGetHost(settings.FIDES_API_URL);
    geolocationApiHost = safelyGetHost(settings.GEOLOCATION_API_URL);
    cachedSettings = true;
  }

  const { contextAppliers, headerDefinitions } = getApplicableHeaderRules(
    request.nextUrl.pathname,
    [
      {
        matcher: /\/.*/,
        headers: [
          ["X-Content-Type-Options", "nosniff"],
          ["Cache-Control", "no-cache, no-store, must-revalidate"],
          ["Strict-Transport-Security", "max-age=3153600"],
        ],
      },
      {
        matcher: /\/?!embedded-consent\.html/,
        headers: [["X-Frame-Options", "deny"]],
      },
      {
        matcher: /\/embedded-consent\.html/,
        headers: [
          [
            CONTENT_SECURITY_POLICY_HEADER,
            staticPageCspHeader({ fidesApiHost, geolocationApiHost }),
          ],
        ],
      },
      {
        matcher: /\/((?!api|_next\/static|_next\/image|favicon\.ico).*)/,
        headers: [
          {
            name: CONTENT_SECURITY_POLICY_HEADER,
            context: (initializer) => {
              if (initializer.hasContext("x-nonce")) {
                return;
              }

              const nonce = Buffer.from(crypto.randomUUID()).toString("base64");
              initializer.setContext("x-nonce", nonce);
            },
            value: (context) => {
              const nonce = context.get("x-nonce") ?? "";
              return privacyCenterPagesCspHeader({
                isDev,
                fidesApiHost,
                geolocationApiHost,
                nonce,
              });
            },
          },
        ],
      },
    ],
  );

  const initializer: MiddlewareResponseInit = {
    request: {
      headers: requestHeaders,
    },
  };

  applyRequestContext(contextAppliers, initializer);

  const response = NextResponse.next(initializer);

  applyResponseHeaders(initializer, headerDefinitions, response);

  return response;
}
