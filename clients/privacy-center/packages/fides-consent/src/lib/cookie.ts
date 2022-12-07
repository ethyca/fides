import { getCookie, setCookie, Types } from "typescript-cookie";

/**
 * A mapping from the cookie keys (configurable strings) to the resolved consent value.
 */
export type CookieKeyConsent = {
  [cookieKey: string]: boolean | undefined;
};

export const CONSENT_COOKIE_NAME = "fides_consent";

export const CONSENT_COOKIE_MAX_AGE_DAYS = 365;

/**
 * The typescript-cookie default codec has a more conservative strategy in order to
 * comply with the exact requirements of RFC 6265. For ease of use in external pages,
 * we instead use encode/decodeURIComponent which are available in every browser.
 *
 * See: https://github.com/carhartl/typescript-cookie#encoding
 */
const CODEC: Types.CookieCodecConfig<string, string> = {
  decodeName: decodeURIComponent,
  decodeValue: decodeURIComponent,
  encodeName: encodeURIComponent,
  encodeValue: encodeURIComponent,
};

export const getConsentCookie = (): CookieKeyConsent => {
  if (typeof document === "undefined") {
    return {};
  }

  const cookie = getCookie(CONSENT_COOKIE_NAME, CODEC);
  if (!cookie) {
    return {};
  }

  try {
    return JSON.parse(cookie);
  } catch (err) {
    // eslint-disable-next-line no-console
    console.error("Unable to read consent cookie: invalid JSON.", err);
    return {};
  }
};

export const setConsentCookie = (cookieKeyConsent: CookieKeyConsent) => {
  if (typeof document === "undefined") {
    return;
  }

  setCookie(
    CONSENT_COOKIE_NAME,
    JSON.stringify(cookieKeyConsent),
    {
      // An explicit domain allows subdomains to access the cookie.
      domain: window.location.hostname,
      expires: CONSENT_COOKIE_MAX_AGE_DAYS,
    },
    CODEC
  );
};
