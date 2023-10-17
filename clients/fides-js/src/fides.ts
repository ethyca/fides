/**
 * Fides.js: Javascript library for Fides (https://github.com/ethyca/fides)
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
import { gtm } from "./integrations/gtm";
import { meta } from "./integrations/meta";
import { shopify } from "./integrations/shopify";

import {
  FidesCookie,
  buildCookieConsentForExperiences,
  isNewFidesCookie,
} from "./lib/cookie";
import {
  FidesConfig,
  FidesOptions,
  PrivacyExperience,
} from "./lib/consent-types";

import { dispatchFidesEvent } from "./lib/events";

import {
  initialize,
  getInitialCookie,
  getInitialFides,
} from "./lib/initialize";
import type { Fides } from "./lib/initialize";

import { renderOverlay } from "./lib/renderOverlay";
import { getConsentContext } from "./lib/consent-context";

declare global {
  interface Window {
    Fides: Fides;
  }
}

// The global Fides object; this is bound to window.Fides if available
// eslint-disable-next-line no-underscore-dangle,@typescript-eslint/naming-convention
let _Fides: Fides;

const updateCookie = async (
  oldCookie: FidesCookie,
  experience: PrivacyExperience,
  debug?: boolean
): Promise<FidesCookie> => {
  const context = getConsentContext();
  const consent = buildCookieConsentForExperiences(
    experience,
    context,
    !!debug
  );
  return { ...oldCookie, consent };
};

type OverrideFidesOptions = Pick<
  FidesOptions,
  "fidesString" | "fidesDisableSaveApi" | "fidesEmbed"
>;

const overrideOptionsValidatorMap = new Map<keyof OverrideFidesOptions, RegExp>(
  [
    ["fidesString", /(.*)/], // for now allow any characters, but follow-up with more strict validation after implementing AC str
    ["fidesDisableSaveApi", /^(?i)(true|false)$/],
    ["fidesEmbed", /^(?i)(true|false)$/],
  ]
);

/**
 * Gets and validates Fides override options provided through URL query params.
 * This function is extensible to further support other methods of override, e.g. cookie or window obj.
 */
const getOverrideFidesOptions = (): Map<string, string> => {
  const overrideOptions: Map<string, string> = new Map();
  if (typeof window !== "undefined") {
    // look for override options on URL query params
    const params = new URLSearchParams(document.location.search);
    overrideOptionsValidatorMap.forEach(
      (regexp: RegExp, optionName: string) => {
        const value = params.get(optionName);
        if (value && regexp.test(value)) {
          overrideOptions.set(optionName, value);
        }
      }
    );
  }
  return overrideOptions;
};

/**
 * Initialize the global Fides object with the given configuration values
 */
const init = async (config: FidesConfig) => {
  const overrideOptions: Map<string, string> = getOverrideFidesOptions();
  // eslint-disable-next-line no-param-reassign
  config.options = { ...config.options, ...overrideOptions };
  const cookie = getInitialCookie(config);
  const initialFides = getInitialFides({ ...config, cookie });
  if (initialFides) {
    Object.assign(_Fides, initialFides);
    dispatchFidesEvent("FidesInitialized", cookie, config.options.debug);
    dispatchFidesEvent("FidesUpdated", cookie, config.options.debug);
  }
  const experience = initialFides?.experience ?? config.experience;
  const updatedFides = await initialize({
    ...config,
    experience,
    cookie,
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
    tcfEnabled: false,
    fidesEmbed: false,
    fidesDisableSaveApi: false,
    fidesString: null,
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

// Export everything from ./lib/* to use when importing fides.mjs as a module
export * from "./components";
export * from "./services/fides/api";
export * from "./services/external/geolocation";
export * from "./lib/consent";
export * from "./lib/consent-context";
export * from "./lib/consent-types";
export * from "./lib/consent-utils";
export * from "./lib/consent-value";
export * from "./lib/cookie";
export * from "./lib/events";
