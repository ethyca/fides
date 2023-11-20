/**
 * Fides-tcf.js: Javascript library for Fides (https://github.com/ethyca/fides), including
 * features for supporting the Transparency Consent Framework
 *
 * This JS module provides easy access to interact with Fides from a webpage, including the ability to:
 * - initialize the page with default consent options (e.g. opt-out of advertising cookies, opt-in to analytics, etc.)
 * - read/write the current user's consent preferences to their browser as a cookie
 * - push the current user's consent preferences to other systems via integrations (Google Tag Manager, Meta, etc.)
 *
 * See https://fid.es for more information!
 *
 * Basic usage of this module in an HTML page is:
 * ```
 * <script src="https://privacy.{company}.com/fides.js"></script>
 * <script>
 *   window.Fides.init({
 *     consent: {
 *       options: [{
 *         cookieKeys: ["data_sales"],
 *         default: true,
 *         fidesDataUseKey: "advertising"
 *       }]
 *     },
 *     experience: {},
 *     geolocation: {},
 *     options: {
 *           debug: true,
 *           isDisabled: false,
 *           isGeolocationEnabled: false,
 *           geolocationApiUrl: "",
 *           overlayParentId: null,
 *           modalLinkId: null,
 *           privacyCenterUrl: "http://localhost:3000"
 *         }
 *   });
 * </script>
 * ```
 *
 * ...and later:
 * ```
 * <script>
 *   // Query user consent preferences
 *   if (window.Fides.consent.data_sales) {
 *     // ...enable advertising scripts
 *   }
 * ```
 */
import type { TCData } from "@iabtechlabtcf/cmpapi";
import { gtm } from "./integrations/gtm";
import { meta } from "./integrations/meta";
import { shopify } from "./integrations/shopify";

import {
  FidesConfig,
  FidesOverrides,
  OverrideOptions,
  PrivacyExperience,
  UserConsentPreference,
} from "./lib/consent-types";

import { generateFidesString, initializeTcfCmpApi } from "./lib/tcf";
import {
  getInitialCookie,
  getInitialFides,
  getOverrides,
  initialize,
} from "./lib/initialize";
import type { Fides } from "./lib/initialize";
import { dispatchFidesEvent } from "./lib/events";
import {
  buildTcfEntitiesFromCookie,
  debugLog,
  experienceIsValid,
  FidesCookie,
  hasSavedTcfPreferences,
  isPrivacyExperience,
  tcfConsentCookieObjHasSomeConsentSet,
  transformTcfPreferencesToCookieKeys,
  transformUserPreferenceToBoolean,
} from "./fides";
import { renderOverlay } from "./lib/tcf/renderOverlay";
import {
  EnabledIds,
  TcfModelsRecord,
  TcfSavePreferences,
} from "./lib/tcf/types";
import { TCF_KEY_MAP } from "./lib/tcf/constants";
import {
  generateFidesStringFromCookieTcfConsent,
  transformFidesStringToCookieKeys,
} from "./lib/tcf/utils";
import type { GppFunction } from "./lib/gpp/types";
import { setupExtensions } from "./extensions/setup";

declare global {
  interface Window {
    Fides: Fides;
    __tcfapiLocator?: Window;
    __tcfapi?: (
      command: string,
      version: number,
      callback: (tcData: TCData, success: boolean) => void,
      parameter?: number | string
    ) => void;
    config: {
      // DEFER (PROD-1243): support a configurable "custom options" path
      tc_info: OverrideOptions;
    };
    __gpp?: GppFunction;
    __gppLocator?: Window;
  }
}

// The global Fides object; this is bound to window.Fides if available
// eslint-disable-next-line no-underscore-dangle,@typescript-eslint/naming-convention
let _Fides: Fides;

/** Helper function to determine the initial value of a TCF object */
const getInitialPreference = (
  tcfObject: TcfModelsRecord
): UserConsentPreference => {
  if (tcfObject.current_preference) {
    return tcfObject.current_preference;
  }
  return tcfObject.default_preference ?? UserConsentPreference.OPT_OUT;
};

const updateCookieAndExperience = async ({
  cookie,
  experience,
  debug = false,
  isExperienceClientSideFetched,
}: {
  cookie: FidesCookie;
  experience: PrivacyExperience;
  debug?: boolean;
  isExperienceClientSideFetched: boolean;
}): Promise<{
  cookie: FidesCookie;
  experience: Partial<PrivacyExperience>;
}> => {
  if (!isExperienceClientSideFetched) {
    // If it's not client side fetched, we don't update anything since the cookie has already
    // been updated earlier.
    return { cookie, experience };
  }

  // If cookie.fides_string exists, update the fetched experience based on the cookie here.
  if (cookie.fides_string) {
    debugLog(
      debug,
      "Overriding preferences from client-side fetched experience with cookie fides_string consent",
      cookie.fides_string
    );
    const tcfEntities = buildTcfEntitiesFromCookie(experience, cookie);
    return { cookie, experience: tcfEntities };
  }

  // If user has no prefs saved, we don't need to override the prefs on the cookie
  if (!hasSavedTcfPreferences(experience)) {
    return { cookie, experience };
  }

  // If the user has prefs on a client-side fetched experience, but there is no fides_string,
  // we need to use the prefs on the experience to generate a fidesString and cookie.tcf_consent
  const tcSavePrefs: TcfSavePreferences = {};
  const enabledIds: EnabledIds = {
    purposesConsent: [],
    purposesLegint: [],
    specialPurposes: [],
    features: [],
    specialFeatures: [],
    vendorsConsent: [],
    vendorsLegint: [],
  };

  TCF_KEY_MAP.forEach(({ experienceKey, cookieKey, enabledIdsKey }) => {
    tcSavePrefs[cookieKey] = [];
    experience[experienceKey]?.forEach((record) => {
      const pref: UserConsentPreference = getInitialPreference(record);
      // map experience to tcSavePrefs (same as cookie keys)
      tcSavePrefs[cookieKey]?.push({
        // @ts-ignore
        id: record.id,
        preference: pref,
      });
      // add to enabledIds only if user consent is True
      if (transformUserPreferenceToBoolean(pref)) {
        if (enabledIdsKey) {
          enabledIds[enabledIdsKey].push(record.id.toString());
        }
      }
    });
  });

  const fidesString = await generateFidesString({
    experience,
    tcStringPreferences: enabledIds,
  });
  const tcfConsent = transformTcfPreferencesToCookieKeys(tcSavePrefs);
  return {
    cookie: { ...cookie, fides_string: fidesString, tcf_consent: tcfConsent },
    experience,
  };
};

/**
 * If a fidesString is provided either explicitly or retrieved with a custom get preferences fn,
 * we override the associated cookie props, which are then used to override associated props in the experience.
 */
const updateFidesCookieFromString = (
  cookie: FidesCookie,
  fidesString: string,
  debug: boolean,
  fidesStringVersionHash: string | undefined
): { cookie: FidesCookie; success: boolean } => {
  debugLog(
    debug,
    "Explicit fidesString detected. Proceeding to override all TCF preferences with given fidesString"
  );
  try {
    const cookieKeys = transformFidesStringToCookieKeys(fidesString, debug);
    return {
      cookie: {
        ...cookie,
        tcf_consent: cookieKeys,
        fides_string: fidesString,
        tcf_version_hash: fidesStringVersionHash ?? cookie.tcf_version_hash,
      },
      success: true,
    };
  } catch (error) {
    debugLog(
      debug,
      `Could not decode tcString from ${fidesString}, it may be invalid. ${error}`
    );
    return { cookie, success: false };
  }
};

/**
 * Initialize the global Fides object with the given configuration values
 */
const init = async (config: FidesConfig) => {
  const overrides: Partial<FidesOverrides> = await getOverrides(config);
  // eslint-disable-next-line no-param-reassign
  config.options = { ...config.options, ...overrides.overrideOptions };
  const cookie = {
    ...getInitialCookie(config),
    ...overrides.overrideConsentPrefs?.consent,
  };
  if (config.options.fidesString) {
    const { cookie: updatedCookie, success } = updateFidesCookieFromString(
      cookie,
      config.options.fidesString,
      config.options.debug,
      overrides.overrideConsentPrefs?.version_hash
    );
    if (success) {
      Object.assign(cookie, updatedCookie);
    }
  } else if (
    tcfConsentCookieObjHasSomeConsentSet(cookie.tcf_consent) &&
    !cookie.fides_string &&
    isPrivacyExperience(config.experience) &&
    experienceIsValid(config.experience, config.options)
  ) {
    // This state should not be hit, but just in case: if fidesString is missing on cookie but we have tcf consent,
    // we should generate fidesString so that our CMP API accurately reflects user preference
    cookie.fides_string = await generateFidesStringFromCookieTcfConsent(
      config.experience,
      cookie.tcf_consent
    );
    debugLog(
      config.options.debug,
      "fides_string was missing from cookie, so it has been generated based on tcf_consent",
      cookie.fides_string
    );
  }
  const initialFides = getInitialFides({ ...config, cookie });
  // Initialize the CMP API early so that listeners are established
  initializeTcfCmpApi();
  if (initialFides) {
    Object.assign(_Fides, initialFides);
    dispatchFidesEvent("FidesInitialized", cookie, config.options.debug);
  }
  const experience = initialFides?.experience ?? config.experience;
  const updatedFides = await initialize({
    ...config,
    cookie,
    experience,
    renderOverlay,
    updateCookieAndExperience,
  });
  Object.assign(_Fides, updatedFides);

  // Dispatch the "FidesInitialized" event to update listeners with the initial state.
  dispatchFidesEvent("FidesInitialized", cookie, config.options.debug);

  // Call extensions
  setupExtensions();
};

// The global Fides object; this is bound to window.Fides if available
_Fides = {
  consent: {},
  experience: undefined,
  geolocation: {},
  options: {
    debug: true,
    isOverlayEnabled: false,
    isPrefetchEnabled: false,
    isGeolocationEnabled: false,
    geolocationApiUrl: "",
    overlayParentId: null,
    modalLinkId: null,
    privacyCenterUrl: "",
    fidesApiUrl: "",
    serverSideFidesApiUrl: "",
    tcfEnabled: true,
    fidesEmbed: false,
    fidesDisableSaveApi: false,
    fidesDisableBanner: false,
    fidesString: null,
    apiOptions: null,
  },
  fides_meta: {},
  identity: {},
  tcf_consent: {},
  gtm,
  init,
  initialized: false,
  meta,
  shopify,
};

if (typeof window !== "undefined") {
  window.Fides = _Fides;
}

// Export everything from ./lib/* to use when importing fides-tcf.mjs as a module
export * from "./components";
export * from "./lib/consent";
export * from "./lib/consent-context";
export * from "./lib/consent-types";
export * from "./lib/consent-utils";
export * from "./lib/consent-value";
export * from "./lib/cookie";
export * from "./lib/events";
