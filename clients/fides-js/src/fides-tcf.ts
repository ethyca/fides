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
  FidesOptionOverrides,
  OverrideOptions,
  PrivacyExperience,
  UserConsentPreference,
} from "./lib/consent-types";

import { generateFidesString, initializeCmpApi } from "./lib/tcf";
import {
  getInitialCookie,
  getInitialFides,
  getOverrideFidesOptions,
  initialize,
} from "./lib/initialize";
import type { Fides } from "./lib/initialize";
import { dispatchFidesEvent } from "./lib/events";
import {
  debugLog,
  experienceIsValid,
  FidesCookie,
  hasSavedTcfPreferences,
  isNewFidesCookie,
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

const updateCookie = async (
  oldCookie: FidesCookie,
  experience: PrivacyExperience
): Promise<FidesCookie> => {
  // ignore server-side prefs if either user has no prefs to override, or TC str override is set
  if (!hasSavedTcfPreferences(experience)) {
    return { ...oldCookie, fides_string: "" };
  }

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
  return { ...oldCookie, fides_string: fidesString, tcf_consent: tcfConsent };
};

/**
 * Initialize the global Fides object with the given configuration values
 */
const init = async (config: FidesConfig) => {
  const overrideOptions: Partial<FidesOptionOverrides> =
    getOverrideFidesOptions();
  // eslint-disable-next-line no-param-reassign
  config.options = { ...config.options, ...overrideOptions };
  const cookie = getInitialCookie(config);
  if (config.options.fidesString) {
    // If a fidesString is explicitly passed in, we override the associated cookie props, which are then used to
    // override associated props in experience
    debugLog(
      config.options.debug,
      "Explicit fidesString detected. Proceeding to override all TCF preferences with given fidesString"
    );
    cookie.fides_string = config.options.fidesString;
    cookie.tcf_consent = transformFidesStringToCookieKeys(
      config.options.fidesString,
      config.options.debug
    );
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
  initializeCmpApi();
  if (initialFides) {
    Object.assign(_Fides, initialFides);
    dispatchFidesEvent("FidesInitialized", cookie, config.options.debug);
    dispatchFidesEvent("FidesUpdated", cookie, config.options.debug);
  }
  const experience = initialFides?.experience ?? config.experience;
  const updatedFides = await initialize({
    ...config,
    cookie,
    experience,
    renderOverlay,
    updateCookie,
  });
  Object.assign(_Fides, updatedFides);

  // Dispatch the "FidesInitialized" event to update listeners with the initial
  // state. Skip if we already initialized due to an existing cookie.
  // For convenience, also dispatch the "FidesUpdated" event; this allows
  // listeners to ignore the initialization event if they prefer
  if (isNewFidesCookie(cookie)) {
    dispatchFidesEvent("FidesInitialized", cookie, config.options.debug);
  }
  dispatchFidesEvent("FidesUpdated", cookie, config.options.debug);
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
