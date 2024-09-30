import { decode as base64_decode, encode as base64_encode } from "base-64";
import Cookies, { CookiesStatic } from "js-cookie";
import { v4 as uuidv4 } from "uuid";

import { ConsentContext } from "./consent-context";
import {
  Cookies as CookiesType,
  FidesCookie,
  LegacyConsentConfig,
  NoticeConsent,
  PrivacyExperience,
  PrivacyNoticeWithPreference,
  SaveConsentPreference,
} from "./consent-types";
import { debugLog } from "./consent-utils";
import { resolveLegacyConsentValue } from "./consent-value";
import {
  transformConsentToFidesUserPreference,
  transformUserPreferenceToBoolean,
} from "./shared-consent-utils";
import { FIDES_SYSTEM_COOKIE_KEY_MAP } from "./tcf/constants";
import type { TcfOtherConsent, TcfSavePreferences } from "./tcf/types";

/**
 * Save the cookie under the name "fides_consent" for 365 days
 */
export const CONSENT_COOKIE_NAME = "fides_consent";
export const CONSENT_COOKIE_MAX_AGE_DAYS = 365;

/**
 * The js-cookie default codec has a more conservative strategy in order to
 * comply with the exact requirements of RFC 6265. For ease of use in external pages,
 * we instead use encode/decodeURIComponent which are available in every browser.
 *
 * See: https://www.npmjs.com/package/js-cookie#converters
 */

const cookies: CookiesStatic = Cookies.withConverter({
  read(value) {
    return decodeURIComponent(value);
  },
  write(value) {
    return encodeURIComponent(value);
  },
});

export const consentCookieObjHasSomeConsentSet = (
  consent: NoticeConsent | undefined,
): boolean => {
  if (!consent) {
    return false;
  }
  return Object.values(consent).some(
    (val: boolean | undefined) => val !== undefined,
  );
};

/**
 * Each cookie will be assigned an autogenerated user/device ID, to match user's
 * consent preferences between the browser and the server. This is a randomly
 * generated UUID to prevent it from being identifiable (without matching it to
 * some other identity data!)
 */
const generateFidesUserDeviceId = (): string => uuidv4();
const userDeviceId = generateFidesUserDeviceId();

/**
 * Determine whether or not the given cookie is "new" (ie. has never been saved
 * to the browser).
 */
export const isNewFidesCookie = (cookie: FidesCookie): boolean => {
  const isSaved = Boolean(cookie.fides_meta?.updatedAt);
  return !isSaved;
};

/**
 * Generate a new Fides cookie with default values for the current user.
 */
export const makeFidesCookie = (consent?: NoticeConsent): FidesCookie => {
  const now = new Date();
  return {
    consent: consent || {},
    identity: {
      fides_user_device_id: userDeviceId || generateFidesUserDeviceId(), // the fallback here is a bit overkill, but it is mostly to make the unit test work since it doesn't have a global context.
    },
    fides_meta: {
      version: "0.9.0",
      createdAt: now.toISOString(),
      updatedAt: "",
    },
    tcf_consent: {},
  };
};

/**
 * Retrieve cookie by name
 */
export const getCookieByName = (cookieName: string): string | undefined =>
  cookies.get(cookieName);

/**
 * Retrieve and decode fides consent cookie
 */
export const getFidesConsentCookie = (
  debug: boolean = false,
): FidesCookie | undefined => {
  const cookieString = getCookieByName(CONSENT_COOKIE_NAME);
  if (!cookieString) {
    return undefined;
  }
  // For safety, always try JSON decoding, and if that fails use BASE64
  try {
    return JSON.parse(cookieString);
  } catch {
    try {
      return JSON.parse(base64_decode(cookieString));
    } catch (e) {
      debugLog(debug, `Unable to read consent cookie`, e);
      return undefined;
    }
  }
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
  defaults?: NoticeConsent,
  debug: boolean = false,
  fidesClearCookie: boolean = false,
): FidesCookie => {
  // Create a default cookie and set the configured consent defaults
  const defaultCookie = makeFidesCookie(defaults);
  if (typeof document === "undefined") {
    return defaultCookie;
  }

  if (fidesClearCookie) {
    document.cookie =
      "fides_consent=; Path=/; Expires=Thu, 01 Jan 1970 00:00:01 GMT";
    return defaultCookie;
  }

  // Check for an existing cookie for this device
  let parsedCookie: FidesCookie | undefined = getFidesConsentCookie();
  if (!parsedCookie) {
    debugLog(
      debug,
      `No existing Fides consent cookie found, returning defaults.`,
      parsedCookie,
    );
    return defaultCookie;
  }

  try {
    // Check format of parsed cookie; if it's structured like we
    // expect, cast it directly. Otherwise, assume it's a previous version of
    // the cookie, which was strictly the consent key/value preferences
    if (!("consent" in parsedCookie && "fides_meta" in parsedCookie)) {
      // Missing the expected format, so we parse it as strictly consent
      // preferences and "wrap" it with the default cookie style
      parsedCookie = {
        ...defaultCookie,
        consent: parsedCookie,
      };
    }

    // Re-apply the default consent values to the parsed cookie; they may have
    // changed, so new defaults should be added. However, ensure that any
    // existing user preferences override those defaults!
    const updatedConsent: NoticeConsent = {
      ...defaults,
      ...parsedCookie.consent,
    };
    parsedCookie.consent = updatedConsent;
    // since console.log is synchronous, we stringify to accurately read the parsedCookie obj
    debugLog(
      debug,
      `Applied existing consent to data from existing Fides consent cookie.`,
      JSON.stringify(parsedCookie),
    );
    return parsedCookie;
  } catch (err) {
    debugLog(debug, `Unable to read consent cookie: invalid JSON.`, err);
    return defaultCookie;
  }
};

/**
 * Save the given Fides cookie to the browser using the current root domain.
 *
 * This calculates the root domain by using the last parts of the hostname:
 *   privacy.example.co.uk -> example.co.uk
 *   privacy.example.com -> example.com
 *   example.com -> example.com
 *   localhost -> localhost
 */
export const saveFidesCookie = (
  cookie: FidesCookie,
  base64Cookie: boolean = false,
) => {
  if (typeof document === "undefined") {
    return;
  }

  // Record the last update time for the cookie
  const now = new Date();
  const updatedAt = now.toISOString();
  // eslint-disable-next-line no-param-reassign
  cookie.fides_meta.updatedAt = updatedAt;

  let encodedCookie: string = JSON.stringify(cookie);
  if (base64Cookie) {
    encodedCookie = base64_encode(encodedCookie);
  }

  const hostnameParts = window.location.hostname.split(".");
  let topViableDomain = "";
  for (let i = 1; i <= hostnameParts.length; i += 1) {
    // This loop guarantees to get the top-level hostname because that's the smallest one browsers will let you set cookies in. We test a given suffix for whether we are able to set cookies, if not we try the next suffix until we find the one that works.
    topViableDomain = hostnameParts.slice(-i).join(".");
    const c = cookies.set(CONSENT_COOKIE_NAME, encodedCookie, {
      // An explicit path ensures this is always set to the entire domain.
      path: "/",
      // An explicit domain allows subdomains to access the cookie.
      domain: topViableDomain,
      expires: CONSENT_COOKIE_MAX_AGE_DAYS,
    });
    if (c) {
      const savedCookie = getFidesConsentCookie();
      // If it's a new cookie, then checking for an existing cookie would be enough. But, if the cookie is being updated then we need to also check if the updatedAt is the same. Otherwise, we would be breaking on the TLD (eg. .com) here.
      if (
        savedCookie &&
        savedCookie.fides_meta.updatedAt === cookie.fides_meta.updatedAt
      ) {
        break;
      }
    }
  }
};

/**
 * Updates prefetched experience, based on:
 * 1) experience: pre-fetched or client-side experience-based consent configuration
 * 2) cookie: cookie containing user preference.
 *
 * Returns updated experience with user preferences.
 */
export const updateExperienceFromCookieConsentNotices = ({
  experience,
  cookie,
  debug,
}: {
  experience: PrivacyExperience;
  cookie: FidesCookie;
  debug?: boolean;
}): PrivacyExperience => {
  // If the given experience has no notices, return immediately and do not mutate
  // the experience object in any way
  if (!experience.privacy_notices) {
    return experience;
  }
  // DEFER (PROD-1568) - instead of updating experience here, push this logic into UI
  const noticesWithConsent: PrivacyNoticeWithPreference[] | undefined =
    experience.privacy_notices?.map((notice) => {
      const preference = Object.keys(cookie.consent).includes(notice.notice_key)
        ? transformConsentToFidesUserPreference(
            Boolean(cookie.consent[notice.notice_key]),
            notice.consent_mechanism,
          )
        : undefined;
      return { ...notice, current_preference: preference };
    });

  if (debug) {
    debugLog(
      debug,
      `Returning updated pre-fetched experience with user consent.`,
      experience,
    );
  }
  return { ...experience, privacy_notices: noticesWithConsent };
};

export const transformTcfPreferencesToCookieKeys = (
  tcfPreferences: TcfSavePreferences,
): TcfOtherConsent => {
  const cookieKeys: TcfOtherConsent = {};
  FIDES_SYSTEM_COOKIE_KEY_MAP.forEach(({ cookieKey }) => {
    const preferences = tcfPreferences[cookieKey] ?? [];
    cookieKeys[cookieKey] = Object.fromEntries(
      preferences.map((pref) => [
        pref.id,
        transformUserPreferenceToBoolean(pref.preference),
      ]),
    );
  });
  return cookieKeys;
};

/**
 * Generate the *default* consent preferences for this session, based on:
 * 1) config: current legacy consent configuration, which defines the options and their
 *    default values (e.g. "data_sales" => true)
 * 2) context: browser context, which can automatically override those defaults
 *    in some cases (e.g. global privacy control => false)
 *
 * Returns the final set of "defaults" that can then be changed according to the
 * user's preferences.
 */
export const makeConsentDefaultsLegacy = (
  config: LegacyConsentConfig | undefined,
  context: ConsentContext,
  debug: boolean,
): NoticeConsent => {
  const defaults: NoticeConsent = {};
  config?.options.forEach(({ cookieKeys, default: current }) => {
    if (current === undefined) {
      return;
    }

    const value = resolveLegacyConsentValue(current, context);

    cookieKeys.forEach((cookieKey) => {
      const previous = defaults[cookieKey];
      if (previous === undefined) {
        defaults[cookieKey] = value;
        return;
      }

      defaults[cookieKey] = previous && value;
    });
  });
  debugLog(debug, `Returning defaults for legacy config.`, defaults);
  return defaults;
};

/**
 * Given a list of cookies, deletes them from the browser
 * This only removes cookies from the current domain and subdomains
 */
export const removeCookiesFromBrowser = (cookiesToRemove: CookiesType[]) => {
  cookiesToRemove.forEach((cookie) => {
    const { hostname } = window.location;
    cookies.remove(cookie.name);
    cookies.remove(cookie.name, { domain: `.${hostname}` });
    // also remove when cookie domain is set; see PROD-2830
    cookies.remove(cookie.name, { domain: cookie.domain });
  });
};

/**
 * Update cookie based on consent preferences to save
 */
export const updateCookieFromNoticePreferences = async (
  oldCookie: FidesCookie,
  consentPreferencesToSave: SaveConsentPreference[],
): Promise<FidesCookie> => {
  const noticeMap = new Map<string, boolean>(
    consentPreferencesToSave.map(({ notice, consentPreference }) => [
      notice.notice_key,
      transformUserPreferenceToBoolean(consentPreference),
    ]),
  );
  const consentCookieKey: NoticeConsent = Object.fromEntries(noticeMap);
  return {
    ...oldCookie,
    consent: consentCookieKey,
  };
};

/**
 * Extract the current consent state from the given PrivacyExperience by
 * iterating through the notices and pulling out the current preferences (or
 * default values). This is used during initialization to override saved cookie
 * values with newer values from the experience.
 */
export const getConsentStateFromExperience = (
  experience: PrivacyExperience,
): NoticeConsent => {
  const consent: NoticeConsent = {};
  if (!experience.privacy_notices) {
    return consent;
  }
  experience.privacy_notices.forEach((notice) => {
    if (notice.current_preference) {
      consent[notice.notice_key] = transformUserPreferenceToBoolean(
        notice.current_preference,
      );
    } else if (notice.default_preference) {
      consent[notice.notice_key] = transformUserPreferenceToBoolean(
        notice.default_preference,
      );
    }
  });
  return consent;
};

/**
 * Update the "cookie" state with any preferences from the given
 * PrivacyExperience. See getConsentStateFromExperience for details.
 */
export const updateCookieFromExperience = ({
  cookie,
  experience,
}: {
  cookie: FidesCookie;
  experience: PrivacyExperience;
}): FidesCookie => {
  const consent = getConsentStateFromExperience(experience);
  return {
    ...cookie,
    consent,
  };
};
