import { v4 as uuidv4 } from "uuid";
import { getCookie, setCookie, Types } from "typescript-cookie";

import { ConsentConfig } from "./consent-config";
import { ConsentContext } from "./consent-context";
import { resolveConsentValue } from "./consent-value";

/**
 * Store the user's consent preferences on the cookie, as key -> boolean pairs, e.g.
 * {
 *   "data_sales": false,
 *   "analytics": true,
 *   ...
 * }
 */
export type CookieKeyConsent = {
  [cookieKey: string]: boolean | undefined;
};

/**
 * Store the user's identity values on the cookie, e.g.
 * {
 *   "fides_user_device_id": "1234-",
 *   "email": "jane@example.com",
 *   ...
 * }
 */
export type CookieIdentity = Record<string, string>;

/**
 * Store metadata about the cookie itself, e.g.
 * {
 *   "version": "0.9.0",
 *   "createdAt": "2023-01-01T12:00:00.000Z",
 *   ...
 * }
 */
export type CookieMeta = Record<string, string>;

export interface FidesCookie {
  consent:  CookieKeyConsent;
  identity: CookieIdentity;
  fides_meta: CookieMeta;
};


/**
 * Save the cookie under the name "fides_consent" for 365 days
 */
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

/**
 * Each cookie will be assigned an autogenerated user/device ID, to match user's
 * consent preferences between the browser and the server. This is a randomly
 * generated UUID to prevent it from being identifiable (without matching it to
 * some other identity data!)
 */
export const generateFidesUserDeviceId = (): string => uuidv4();

/**
 * Generate a new Fides cookie with default values for the current user.
 */
export const makeFidesCookie = (consent?: CookieKeyConsent): FidesCookie => {
  const now = new Date();
  const userDeviceId = generateFidesUserDeviceId();
  return {
    consent: consent || {},
    identity: {
      "fides_user_device_id": userDeviceId,
    },
    fides_meta: {
      "version": "0.9.0",
      "createdAt": now.toISOString(),
    },
  };
};

/**
 * Generate the *default* consent preferences for this session, based on:
 * 1) config: current consent configuration, which defines the options and their
 *    default values (e.g. "data_sales" => true)
 * 2) context: browser context, which can automatically override those defaults
 *    in some cases (e.g. global privacy control => false)
 * 
 * Returns the final set of "defaults" that can then be changed according to the
 * user's preferences.
 */
export const makeConsentDefaults = ({
  config,
  context,
}: {
  config: ConsentConfig;
  context: ConsentContext;
}): CookieKeyConsent => {
  const defaults: CookieKeyConsent = {};
  config.options.forEach(({ cookieKeys, default: current }) => {
    if (current === undefined) {
      return;
    }

    const value = resolveConsentValue(current, context);

    cookieKeys.forEach((cookieKey) => {
      const previous = defaults[cookieKey];
      if (previous === undefined) {
        defaults[cookieKey] = value;
        return;
      }

      defaults[cookieKey] = previous && value;
    });
  });

  return defaults;
};

/**
 * Attempt to read, parse, and return the current Fides cookie from the browser.
 * If one doesn't exist, make a new default cookie (including generating a new
 * pseudonymous ID) and return the default values.
 * 
 * NOTE: This doesn't *save* the cookie to the browser. To do that, call
 * `saveFidesCookie` with a valid cookie after editing the values.
 */
export const getOrMakeFidesCookie = (
  defaults?: CookieKeyConsent
): FidesCookie => {

  // Create a default cookie and set the configured consent defaults
  const defaultCookie = makeFidesCookie(defaults);

  if (typeof document === "undefined") {
    return defaultCookie;
  }

  // Check for an existing cookie for this device
  const cookieString = getCookie(CONSENT_COOKIE_NAME, CODEC);
  if (!cookieString) {
    return defaultCookie;
  }

  try {
    // Parse the cookie and check it's format; if it's structured like we
    // expect, cast it directly. Otherwise, assume it's a previous version of
    // the cookie, which was strictly the consent key/value preferences
    let parsedCookie: FidesCookie;
    const parsedJson = JSON.parse(cookieString);
    if ("consent" in parsedJson && "fides_meta" in parsedJson) {
      // Matches the expected format, so we can use it as-is
      parsedCookie = parsedJson;
    } else {
      // Missing the expected format, so we parse it as strictly consent
      // preferences and "wrap" it with the default cookie style
      parsedCookie = {
        ...defaultCookie,
        consent: parsedJson,
      }
    }

    // Re-apply the default consent values to the parsed cookie; they may have
    // changed, so new defaults should be added. However, ensure that any
    // existing user preferences override those defaults!
    const updatedConsent: CookieKeyConsent = {
      ...defaults,
      ...parsedCookie.consent,
    }
    parsedCookie.consent = updatedConsent;
    return parsedCookie;
  } catch (err) {
    // eslint-disable-next-line no-console
    console.error("Unable to read consent cookie: invalid JSON.", err);
    return defaultCookie;
  }
};

/**
 * Save the given Fides cookie to the browser using the current root domain.
 * 
 * This calculates the root domain by using the last two parts of the hostname:
 *   privacy.example.com -> example.com
 *   example.com -> example.com
 *   localhost -> localhost
 * 
 * NOTE: This won't handled second-level domains like co.uk:
 *   privacy.example.co.uk -> co.uk # ERROR
 * 
 * (see https://github.com/ethyca/fides/issues/2072)
 */
export const saveFidesCookie = (cookie: FidesCookie) => {
  if (typeof document === "undefined") {
    return;
  }

  const rootDomain = window.location.hostname.split(".").slice(-2).join(".");

  setCookie(
    CONSENT_COOKIE_NAME,
    JSON.stringify(cookie),
    {
      // An explicit domain allows subdomains to access the cookie.
      domain: rootDomain,
      expires: CONSENT_COOKIE_MAX_AGE_DAYS,
    },
    CODEC
  );
};
