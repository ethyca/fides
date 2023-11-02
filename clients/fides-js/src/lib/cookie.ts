import { v4 as uuidv4 } from "uuid";
import { getCookie, removeCookie, setCookie, Types } from "typescript-cookie";

import { ConsentContext } from "./consent-context";
import {
  resolveConsentValue,
  resolveLegacyConsentValue,
} from "./consent-value";
import {
  ConsentMechanism,
  Cookies,
  ExperienceMeta,
  LegacyConsentConfig,
  PrivacyExperience,
  SaveConsentPreference,
} from "./consent-types";
import {
  debugLog,
  transformConsentToFidesUserPreference,
  transformUserPreferenceToBoolean,
} from "./consent-utils";
import type { TcfCookieConsent, TcfSavePreferences } from "./tcf/types";
import { TCF_KEY_MAP } from "./tcf/constants";
import { TcfCookieKeyConsent } from "./tcf/types";

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
  consent: CookieKeyConsent;
  identity: CookieIdentity;
  fides_meta: CookieMeta;
  fides_string?: string;
  tcf_consent: TcfCookieConsent;
  tcf_version_hash?: ExperienceMeta["version_hash"];
}

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

export const tcfConsentCookieObjHasSomeConsentSet = (
  tcf_consent: TcfCookieConsent | undefined
): boolean => {
  if (!tcf_consent) {
    return false;
  }
  return Object.values(tcf_consent).some(
    (val: TcfCookieKeyConsent) => Object.keys(val).length >= 0
  );
};

/**
 * Each cookie will be assigned an autogenerated user/device ID, to match user's
 * consent preferences between the browser and the server. This is a randomly
 * generated UUID to prevent it from being identifiable (without matching it to
 * some other identity data!)
 */
export const generateFidesUserDeviceId = (): string => uuidv4();

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
export const makeFidesCookie = (consent?: CookieKeyConsent): FidesCookie => {
  const now = new Date();
  const userDeviceId = generateFidesUserDeviceId();
  return {
    consent: consent || {},
    identity: {
      fides_user_device_id: userDeviceId,
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
  getCookie(cookieName, CODEC);

/**
 * Attempt to read, parse, and return the current Fides cookie from the browser.
 * If one doesn't exist, make a new default cookie (including generating a new
 * pseudonymous ID) and return the default values.
 *
 * NOTE: This doesn't *save* the cookie to the browser. To do that, call
 * `saveFidesCookie` with a valid cookie after editing the values.
 */
export const getOrMakeFidesCookie = (
  defaults?: CookieKeyConsent,
  debug: boolean = false
): FidesCookie => {
  // Create a default cookie and set the configured consent defaults
  const defaultCookie = makeFidesCookie(defaults);

  if (typeof document === "undefined") {
    return defaultCookie;
  }

  // Check for an existing cookie for this device
  const cookieString = getCookieByName(CONSENT_COOKIE_NAME);
  if (!cookieString) {
    debugLog(
      debug,
      `No existing Fides consent cookie found, returning defaults.`,
      cookieString
    );
    return defaultCookie;
  }

  try {
    // Parse the cookie and check its format; if it's structured like we
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
      };
    }

    // Re-apply the default consent values to the parsed cookie; they may have
    // changed, so new defaults should be added. However, ensure that any
    // existing user preferences override those defaults!
    const updatedConsent: CookieKeyConsent = {
      ...defaults,
      ...parsedCookie.consent,
    };
    parsedCookie.consent = updatedConsent;
    // since console.log is synchronous, we stringify to accurately read the parsedCookie obj
    debugLog(
      debug,
      `Applied existing consent to data from existing Fides consent cookie.`,
      JSON.stringify(parsedCookie)
    );
    return parsedCookie;
  } catch (err) {
    // eslint-disable-next-line no-console
    debugLog(debug, `Unable to read consent cookie: invalid JSON.`, err);
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
 * NOTE: This won't handle second-level domains like co.uk:
 *   privacy.example.co.uk -> co.uk # ERROR
 *
 * (see https://github.com/ethyca/fides/issues/2072)
 */
export const saveFidesCookie = (cookie: FidesCookie) => {
  if (typeof document === "undefined") {
    return;
  }

  // Record the last update time for the cookie
  const now = new Date();
  const updatedAt = now.toISOString();
  // eslint-disable-next-line no-param-reassign
  cookie.fides_meta.updatedAt = updatedAt;

  // Write the cookie to the root domain
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

/**
 * Builds consent preferences for this session, based on:
 * 1) context: browser context, which can automatically override those defaults
 *    in some cases (e.g. global privacy control => false)
 * 2) experience: current experience-based consent configuration.
 *
 * Returns cookie consent that can then be changed according to the
 * user's preferences.
 */
export const buildCookieConsentForExperiences = (
  experience: PrivacyExperience,
  context: ConsentContext,
  debug: boolean
): CookieKeyConsent => {
  const cookieConsent: CookieKeyConsent = {};
  if (!experience.privacy_notices) {
    return cookieConsent;
  }
  experience.privacy_notices.forEach((notice) => {
    cookieConsent[notice.notice_key] = resolveConsentValue(notice, context);
  });
  debugLog(debug, `Returning cookie consent for experiences.`, cookieConsent);
  return cookieConsent;
};

/**
 * Populates TCF entities with items from cookie.tcf_consent.
 * Returns TCF entities to be assigned to an experience.
 */
export const buildTcfEntitiesFromCookie = (
  experience: PrivacyExperience,
  cookie: FidesCookie
) => {
  const tcfEntities = {
    tcf_purpose_consents: experience.tcf_purpose_consents,
    tcf_purpose_legitimate_interests:
      experience.tcf_purpose_legitimate_interests,
    tcf_special_purposes: experience.tcf_special_purposes,
    tcf_features: experience.tcf_features,
    tcf_special_features: experience.tcf_special_features,
    tcf_vendor_consents: experience.tcf_vendor_consents,
    tcf_vendor_legitimate_interests: experience.tcf_vendor_legitimate_interests,
    tcf_system_consents: experience.tcf_system_consents,
    tcf_system_legitimate_interests: experience.tcf_system_legitimate_interests,
  };

  if (cookie.tcf_consent) {
    TCF_KEY_MAP.forEach(({ cookieKey, experienceKey }) => {
      const cookieConsent = cookie.tcf_consent[cookieKey] ?? {};
      // @ts-ignore the array map should ensure we will get the right record type
      tcfEntities[experienceKey] = experience[experienceKey]?.map((item) => {
        const preference = Object.hasOwn(cookieConsent, item.id)
          ? transformConsentToFidesUserPreference(
              Boolean(cookieConsent[item.id]),
              ConsentMechanism.OPT_IN
            )
          : // if experience contains a tcf entity not defined by tcfEntities, we override experience current pref with the default pref
            item.default_preference;
        return { ...item, current_preference: preference };
      });
    });
  }
  return tcfEntities;
};

/**
 * Updates prefetched experience, based on:
 * 1) experience: pre-fetched experience-based consent configuration that does not contain user preference.
 * 2) cookie: cookie containing user preference.
 *
 * Returns updated experience with user preferences.
 */
export const updateExperienceFromCookieConsent = ({
  experience,
  cookie,
  debug,
}: {
  experience: PrivacyExperience;
  cookie: FidesCookie;
  debug?: boolean;
}): PrivacyExperience => {
  const noticesWithConsent = experience.privacy_notices?.map((notice) => {
    const preference = Object.hasOwn(cookie.consent, notice.notice_key)
      ? transformConsentToFidesUserPreference(
          Boolean(cookie.consent[notice.notice_key]),
          notice.consent_mechanism
        )
      : undefined;
    return { ...notice, current_preference: preference };
  });

  // Handle the TCF case, which has many keys to query
  const tcfEntities = buildTcfEntitiesFromCookie(experience, cookie);

  if (debug) {
    debugLog(
      debug,
      `Returning updated pre-fetched experience with user consent.`,
      experience
    );
  }
  return { ...experience, ...tcfEntities, privacy_notices: noticesWithConsent };
};

export const transformTcfPreferencesToCookieKeys = (
  tcfPreferences: TcfSavePreferences
): TcfCookieConsent => {
  const cookieKeys: TcfCookieConsent = {};
  TCF_KEY_MAP.forEach(({ cookieKey }) => {
    const preferences = tcfPreferences[cookieKey] ?? [];
    cookieKeys[cookieKey] = Object.fromEntries(
      preferences.map((pref) => [
        pref.id,
        transformUserPreferenceToBoolean(pref.preference),
      ])
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
  debug: boolean
): CookieKeyConsent => {
  const defaults: CookieKeyConsent = {};
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
 */
export const removeCookiesFromBrowser = (cookies: Cookies[]) => {
  cookies.forEach((cookie) => {
    removeCookie(cookie.name, {
      path: cookie.path ?? "/",
      domain: cookie.domain,
    });
  });
};

/**
 * Update cookie based on consent preferences to save
 */
export const updateCookieFromNoticePreferences = async (
  oldCookie: FidesCookie,
  consentPreferencesToSave: SaveConsentPreference[]
): Promise<FidesCookie> => {
  const noticeMap = new Map<string, boolean>(
    consentPreferencesToSave.map(({ notice, consentPreference }) => [
      notice.notice_key,
      transformUserPreferenceToBoolean(consentPreference),
    ])
  );
  const consentCookieKey: CookieKeyConsent = Object.fromEntries(noticeMap);
  return {
    ...oldCookie,
    consent: consentCookieKey,
  };
};
