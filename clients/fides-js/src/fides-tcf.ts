/**
 * FidesJS: JavaScript SDK for Fides (https://github.com/ethyca/fides)
 *
 * This is the primary entry point for the fides-tcf.js module, which includes
 * everything from fides.js plus adds support for the IAB Transparency and
 * Consent Framework (TCF).
 *
 * See the overall package docs in ./docs/README.md for more!
 */
import type { TCData } from "@iabtechlabtcf/cmpapi";
import { TCString } from "@iabtechlabtcf/core";
import { gtm } from "./integrations/gtm";
import { meta } from "./integrations/meta";
import { shopify } from "./integrations/shopify";

import {
  FidesConfig,
  FidesExperienceTranslationOverrides,
  FidesGlobal,
  FidesInitOptionsOverrides,
  FidesOptions,
  FidesOverrides,
  GetPreferencesFnResp,
  NoticeConsent,
  OverrideType,
  PrivacyExperience,
} from "./lib/consent-types";

import { initializeTcfCmpApi } from "./lib/tcf";
import {
  getInitialCookie,
  getInitialFides,
  getOverridesByType,
  initialize,
} from "./lib/initialize";
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
import { DEFAULT_MODAL_LINK_LABEL } from "./lib/i18n";

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
async function init(this: FidesGlobal, config: FidesConfig) {
  this.prevConfig = config;
  const optionsOverrides: Partial<FidesInitOptionsOverrides> =
    getOverridesByType<Partial<FidesInitOptionsOverrides>>(
      OverrideType.OPTIONS,
      config
    );
  makeStub({
    gdprAppliesDefault: optionsOverrides?.fidesTcfGdprApplies,
  });
  const experienceTranslationOverrides: Partial<FidesExperienceTranslationOverrides> =
    getOverridesByType<Partial<FidesExperienceTranslationOverrides>>(
      OverrideType.EXPERIENCE_TRANSLATION,
      config
    );
  const consentPrefsOverrides: GetPreferencesFnResp | null =
    await customGetConsentPreferences(config);
  // if we don't already have a fidesString override, use fidesString from consent prefs if they exist
  if (!optionsOverrides.fidesString && consentPrefsOverrides?.fides_string) {
    optionsOverrides.fidesString = consentPrefsOverrides.fides_string;
  }
  const overrides: Partial<FidesOverrides> = {
    optionsOverrides,
    consentPrefsOverrides,
    experienceTranslationOverrides,
  };
  // eslint-disable-next-line no-param-reassign
  config = {
    ...config,
    options: { ...config.options, ...overrides.optionsOverrides },
  };
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
    Object.assign(this, initialFides);
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
    overrides,
  });
  Object.assign(this, updatedFides);

  // Dispatch the "FidesInitialized" event to update listeners with the initial state.
  dispatchFidesEvent("FidesInitialized", cookie, config.options.debug);
};

// The global Fides object; this is bound to window.Fides if available
// eslint-disable-next-line no-underscore-dangle,@typescript-eslint/naming-convention
const _Fides: FidesGlobal = {
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
    fidesPrimaryColor: null,
  },
  fides_meta: {},
  identity: {},
  tcf_consent: {},
  saved_consent: {},
  gtm,
  init,
  prevConfig: undefined,
  reinit() {
    if (!this.prevConfig || !this.initialized) {
      throw new Error("Fides must be initialized before reinitializing");
    }
    return this.init(this.prevConfig);
  },
  initialized: false,
  meta,
  shopify,
  showModal: defaultShowModal,
  getModalLinkLabel: () => DEFAULT_MODAL_LINK_LABEL,
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
