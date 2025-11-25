import { NextResponse } from "next/server";

export interface MiddlewareResponseInit {
  request: { headers: Headers };
}

function isExactMatch(matcher: RegExp, pathname: string) {
  const matchedContent = matcher.exec(pathname);
  const isIncludedPath =
    ((matchedContent ?? [])[0]?.length ?? 0) === pathname.length;
  return isIncludedPath;
}

type SimpleHeader = [string, string];

interface ContextController {
  hasContext: (name: string) => boolean;
  setContext: (name: string, value: string) => void;
  getContext: (name: string) => string | null;
}

type ContextHandler = (args: ContextController) => void;

interface DynamicHeader {
  name: string;
  context?: ContextHandler;
  value: (context: Headers) => string;
}

type HeaderDefinition = SimpleHeader | DynamicHeader;

export interface HeaderRule {
  matcher: RegExp;
  headers: HeaderDefinition[];
}

export const X_NONCE_HEADER = "x-nonce";
export const CONTENT_SECURITY_POLICY_HEADER = "Content-Security-Policy";

export function getApplicableHeaderRules(
  pathname: string,
  headerRules: HeaderRule[],
) {
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

export function applyRequestContext(
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

export function applyResponseHeaders(
  middlewareResponseInitializer: MiddlewareResponseInit,
  headerDefinitions: HeaderDefinition[],
  response: NextResponse,
): void {
  // Docs say that we shouldn't do this, but we have historically been doing
  // it since at least the logging changes. Should we change this?
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
