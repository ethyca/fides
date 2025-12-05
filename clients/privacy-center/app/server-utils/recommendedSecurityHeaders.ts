import {
  CONTENT_SECURITY_POLICY_HEADER,
  HeaderRule,
  X_NONCE_HEADER,
} from "./headers";

const flattenHeader = (header: string) => header.replace(/\s{2,}/g, " ").trim();

export const staticPageCspHeader = (args: {
  fidesApiHost: string;
  geolocationApiHost: string;
}) =>
  flattenHeader(`
    default-src 'self';
    script-src 'self' 'unsafe-inline';
    style-src 'self' 'unsafe-inline';
    connect-src 'self' ${args.fidesApiHost} ${args.geolocationApiHost};
    img-src 'self' blob: data:;
    font-src 'self';
    object-src 'none';
    base-uri 'self';
    form-action 'self';
    frame-ancestors 'self';
    upgrade-insecure-requests;
`);

export const embeddedConsentCspHeader = (args: {
  fidesApiHost: string;
  geolocationApiHost: string;
}) =>
  flattenHeader(`
    default-src 'self';
    script-src 'self' 'unsafe-inline';
    style-src 'self' 'unsafe-inline';
    connect-src 'self' ${args.fidesApiHost} ${args.geolocationApiHost};
    img-src 'self' blob: data:;
    font-src 'self';
    object-src 'none';
    base-uri 'self';
    form-action 'self';
    upgrade-insecure-requests;
`);

export const privacyCenterPagesCspHeader = (args: {
  isDev: boolean;
  fidesApiHost: string;
  geolocationApiHost: string;
  nonce: string;
}) =>
  flattenHeader(`
    default-src 'self';
    script-src 'self' 'nonce-${args.nonce}' 'strict-dynamic' ${args.isDev ? "'unsafe-eval'" : ""};
    style-src 'self' ${args.isDev ? "'unsafe-inline'" : `'nonce-${args.nonce}'`};
    connect-src 'self' ${args.fidesApiHost} ${args.geolocationApiHost};
    img-src 'self' blob: data:;
    font-src 'self';
    object-src 'none';
    base-uri 'self';
    form-action 'self';
    frame-ancestors 'self';
    upgrade-insecure-requests;
`);

export const recommendedSecurityHeaders = (
  isDev: boolean,
  fidesApiHost: string,
  geolocationApiHost: string,
): HeaderRule[] => {
  return [
    {
      matcher: /\/.*/,
      headers: [
        ["X-Content-Type-Options", "nosniff"],
        ["Strict-Transport-Security", "max-age=31536000"],
      ],
    },
    {
      matcher: /\/((?!embedded-consent\.html).*)/,
      headers: [["X-Frame-Options", "SAMEORIGIN"]],
    },
    {
      matcher: /\/(fides-js-components.demo.html|fides-js-demo.html)/,
      headers: [
        {
          name: CONTENT_SECURITY_POLICY_HEADER,
          value: () =>
            staticPageCspHeader({ fidesApiHost, geolocationApiHost }),
        },
      ],
    },
    {
      matcher: /\/embedded-consent.html/,
      headers: [
        {
          name: CONTENT_SECURITY_POLICY_HEADER,
          value: () =>
            embeddedConsentCspHeader({ fidesApiHost, geolocationApiHost }),
        },
      ],
    },
    {
      // Matcher derived from: https://nextjs.org/docs/15/pages/guides/content-security-policy#adding-a-nonce-with-middleware
      matcher: /\/((?!api|_next\/static|_next\/image|favicon\.ico).*)/,
      headers: [
        {
          name: CONTENT_SECURITY_POLICY_HEADER,
          context: (initializer) => {
            if (initializer.hasContext(X_NONCE_HEADER)) {
              return;
            }

            const nonce = Buffer.from(crypto.randomUUID()).toString("base64");
            initializer.setContext(X_NONCE_HEADER, nonce);
          },
          value: (context) => {
            const nonce = context.get(X_NONCE_HEADER) ?? "";
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
  ];
};
