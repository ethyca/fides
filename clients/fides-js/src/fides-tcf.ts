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
import { TCString } from "@iabtechlabtcf/core";
import { gtm } from "./integrations/gtm";
import { meta } from "./integrations/meta";
import { shopify } from "./integrations/shopify";

import {
  NoticeConsent,
  FidesConfig,
  FidesInitOptionsOverrides,
  FidesOverrides,
  GetPreferencesFnResp,
  FidesOptions,
  PrivacyExperience,
} from "./lib/consent-types";

import { initializeTcfCmpApi } from "./lib/tcf";
import {
  getInitialCookie,
  getInitialFides,
  getOptionsOverrides,
  initialize,
} from "./lib/initialize";
import type { FidesGlobal } from "./lib/initialize";
import { dispatchFidesEvent } from "./lib/events";
import { debugLog, FidesCookie, defaultShowModal } from "./fides";
import { renderOverlay } from "./lib/tcf/renderOverlay";
import type { GppFunction } from "./lib/gpp/types";
import { makeStub } from "./lib/tcf/stub";
import { customGetConsentPreferences } from "./services/external/preferences";
import { decodeFidesString } from "./lib/tcf/fidesString";
import {
  buildTcfEntitiesFromCookieAndFidesString,
  updateExperienceFromCookieConsentTcf,
} from "./lib/tcf/utils";

declare global {
  interface Window {
    Fides: FidesGlobal;
    fides_overrides: FidesOptions;
    __tcfapiLocator?: Window;
    __tcfapi?: (
      command: string,
      version: number,
      callback: (tcData: TCData, success: boolean) => void,
      parameter?: number | string
    ) => void;
    __gpp?: GppFunction;
    __gppLocator?: Window;
  }
}

// The global Fides object; this is bound to window.Fides if available
// eslint-disable-next-line no-underscore-dangle,@typescript-eslint/naming-convention
let _Fides: FidesGlobal;

const updateExperience = ({
  cookie,
  experience,
  debug = false,
  isExperienceClientSideFetched,
}: {
  cookie: FidesCookie;
  experience: PrivacyExperience;
  debug?: boolean;
  isExperienceClientSideFetched: boolean;
}): Partial<PrivacyExperience> => {
  if (!isExperienceClientSideFetched) {
    // If it's not client side fetched, we don't update anything since the cookie has already
    // been updated earlier.
    return experience;
  }

  // We need the cookie.fides_string to attach user preference to an experience.
  // If this does not exist, we should assume no user preference has been given and leave the experience as is.
  if (cookie.fides_string) {
    debugLog(
      debug,
      "Overriding preferences from client-side fetched experience with cookie fides_string consent",
      cookie.fides_string
    );
    const tcfEntities = buildTcfEntitiesFromCookieAndFidesString(
      experience,
      cookie
    );
    return tcfEntities;
  }

  return experience;
};

/**
 * Initialize the global Fides object with the given configuration values
 */
const init = async (config: FidesConfig) => {
  const optionsOverrides: Partial<FidesInitOptionsOverrides> =
    getOptionsOverrides(config);
  makeStub({
    gdprAppliesDefault: optionsOverrides?.fidesTcfGdprApplies,
  });
  const consentPrefsOverrides: GetPreferencesFnResp | null =
    await customGetConsentPreferences(config);
  // if we don't already have a fidesString override, use fidesString from consent prefs if they exist
  if (!optionsOverrides.fidesString && consentPrefsOverrides?.fides_string) {
    optionsOverrides.fidesString = consentPrefsOverrides.fides_string;
  }
  const overrides: Partial<FidesOverrides> = {
    optionsOverrides,
    consentPrefsOverrides,
  };
  // eslint-disable-next-line no-param-reassign
  config.options = { ...config.options, ...overrides.optionsOverrides };
  const cookie = {
    ...getInitialCookie(config),
    ...overrides.consentPrefsOverrides?.consent,
  };

  // Keep a copy of saved consent from the cookie, since we update the "cookie"
  // value during initialization based on overrides, experience, etc.
  const savedConsent: NoticeConsent = {
    ...cookie.consent,
  };

  // Update the fidesString if we have an override and the TC portion is valid
  const { fidesString } = config.options;
  if (fidesString) {
    try {
      // Make sure TC string is valid before we assign it
      const { tc: tcString } = decodeFidesString(fidesString);
      TCString.decode(tcString);
      const updatedCookie: Partial<FidesCookie> = {
        fides_string: fidesString,
        tcf_version_hash:
          overrides.consentPrefsOverrides?.version_hash ??
          cookie.tcf_version_hash,
      };
      Object.assign(cookie, updatedCookie);
    } catch (error) {
      debugLog(
        config.options.debug,
        `Could not decode tcString from ${fidesString}, it may be invalid. ${error}`
      );
    }
  }
  const initialFides = getInitialFides({
    ...config,
    cookie,
    savedConsent,
    updateExperienceFromCookieConsent: updateExperienceFromCookieConsentTcf,
  });
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
    savedConsent,
    experience,
    renderOverlay,
    updateExperience,
  });
  Object.assign(_Fides, updatedFides);

  // Dispatch the "FidesInitialized" event to update listeners with the initial state.
  dispatchFidesEvent("FidesInitialized", cookie, config.options.debug);
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
    fidesTcfGdprApplies: true,
    fidesJsBaseUrl: "",
    customOptionsPath: null,
    preventDismissal: false,
    allowHTMLDescription: null,
    base64Cookie: false,
    fidesPreviewMode: false,
  },
  fides_meta: {},
  identity: {},
  tcf_consent: {},
  saved_consent: {},
  gtm,
  init,
  initialized: false,
  meta,
  shopify,
  showModal: defaultShowModal,
};

if (typeof window !== "undefined") {
  window.Fides = _Fides;
}

// Export everything from ./lib/* to use when importing fides-tcf.mjs as a module
export * from "./lib/consent";
export * from "./lib/consent-context";
export * from "./lib/consent-types";
export * from "./lib/consent-utils";
export * from "./lib/shared-consent-utils";
export * from "./lib/consent-value";
export * from "./lib/cookie";
export * from "./lib/events";
