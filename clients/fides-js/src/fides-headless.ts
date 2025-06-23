/**
 * FidesJS: JavaScript SDK for Fides (https://github.com/ethyca/fides)
 *
 * This is the primary entry point for the fides.js module, excluding the UI.
 *
 * See the overall package docs in ./docs/README.md for more!
 */
import {
  FidesConfig,
  FidesCookie,
  FidesExperienceTranslationOverrides,
  FidesGlobal,
  FidesInitOptionsOverrides,
  FidesOverrides,
  GetPreferencesFnResp,
  NoticeValues,
  OverrideType,
} from "./lib/consent-types";
import {
  isNewFidesCookie,
  updateExperienceFromCookieConsentNotices,
} from "./lib/cookie";
import { initializeDebugger } from "./lib/debugger";
import { dispatchFidesEvent } from "./lib/events";
import { DecodedFidesString, decodeFidesString } from "./lib/fides-string";
import {
  getCoreFides,
  raise,
  updateExperience,
  updateWindowFides,
} from "./lib/init-utils";
import {
  getInitialCookie,
  getInitialFidesFromConsentCookie,
  getOverridesByType,
  initialize,
} from "./lib/initialize";
import { customGetConsentPreferences } from "./services/external/preferences";

/**
 * Initialize the global Fides object with the given configuration values
 */
async function init(this: FidesGlobal, providedConfig?: FidesConfig) {
  // confused by the "this"? see https://www.typescriptlang.org/docs/handbook/2/functions.html#declaring-this-in-a-function

  // Initialize Fides with the global configuration object if it exists, or the provided one. If neither exists, raise an error.
  let config =
    providedConfig ??
    (this.config as FidesConfig) ??
    raise("Fides must be initialized with a configuration object");

  initializeDebugger(!!config.options?.debug);

  this.config = config; // no matter how the config is set, we want to store it on the global object

  dispatchFidesEvent("FidesInitializing", undefined, {
    gppEnabled:
      this.config.options.gppEnabled ||
      this.config.experience?.gpp_settings?.enabled,
    tcfEnabled: this.config.options.tcfEnabled,
  });

  const optionsOverrides: Partial<FidesInitOptionsOverrides> =
    getOverridesByType<Partial<FidesInitOptionsOverrides>>(
      OverrideType.OPTIONS,
      config,
    );
  const experienceTranslationOverrides: Partial<FidesExperienceTranslationOverrides> =
    getOverridesByType<Partial<FidesExperienceTranslationOverrides>>(
      OverrideType.EXPERIENCE_TRANSLATION,
      config,
    );
  // DEFER: not implemented - ability to override Fides consent with OneTrust overrides
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
  config = {
    ...config,
    options: { ...config.options, ...overrides.optionsOverrides },
  };
  this.cookie = {
    ...getInitialCookie(config),
  };

  // Keep a copy of saved consent from the cookie, since we update the "cookie"
  // value during initialization based on overrides, experience, etc.
  this.saved_consent = {
    ...(this.cookie.consent as NoticeValues),
  };

  // Update the fidesString if we have an override and the NC portion is valid
  const { fidesString } = config.options;
  if (fidesString) {
    try {
      // Make sure Notice Consent string is valid before we assign it
      const { nc: ncString }: DecodedFidesString =
        decodeFidesString(fidesString);
      this.decodeNoticeConsentString(ncString);
      const updatedCookie: Partial<FidesCookie> = {
        fides_string: fidesString,
      };
      this.cookie = { ...this.cookie, ...updatedCookie };
    } catch (error) {
      fidesDebugger(
        `Could not decode ncString from ${fidesString}, it may be invalid. ${error}`,
      );
    }
  }

  this.experience = config.experience; // pre-fetched experience if available
  const hasExistingCookie = !isNewFidesCookie(this.cookie);
  if (hasExistingCookie) {
    /*
     * We have enough information to initialize the Fides object before we have a valid experience.
     * In this case, the experience is less important because the user has already consented to something.
     * The earlier we can communicate consent to the vendor, the better.
     */
    const initialFides = getInitialFidesFromConsentCookie({
      ...config,
      cookie: this.cookie,
      savedConsent: this.saved_consent,
      updateExperienceFromCookieConsent:
        updateExperienceFromCookieConsentNotices,
    });
    Object.assign(this, initialFides);
    updateWindowFides(this);
    this.experience = initialFides.experience; // pre-fetched experience, if available, with consent applied

    // Vendors (GTM, etc.) can use this event to know when the consent is loaded.
    dispatchFidesEvent("FidesConsentLoaded", this.cookie, {
      shouldShowExperience: this.shouldShowExperience(),
    });
    /** @deprecated - FidesInitialized is used for backwards compatibility only */
    // dispatchFidesEvent("FidesInitialized", this.cookie, {
    //   shouldShowExperience: this.shouldShowExperience(),
    // });
  }

  const updatedFides = await initialize({
    ...config,
    fides: this,
    updateExperience,
    overrides,
    propertyId: config.propertyId,
  });
  Object.assign(this, updatedFides);
  updateWindowFides(this);

  // The window.Fides object and the Overlay are now fully initialized and ready to be used.
  dispatchFidesEvent("FidesReady", this.cookie, {
    shouldShowExperience: this.shouldShowExperience(),
  });
  /** @deprecated - FidesInitialized is used for backwards compatibility only */
  dispatchFidesEvent("FidesInitialized", this.cookie, {
    shouldShowExperience: this.shouldShowExperience(),
  });
}

const initialFides = getCoreFides({});
// The global Fides object; this is bound to window.Fides if available
// eslint-disable-next-line no-underscore-dangle,@typescript-eslint/naming-convention
const _Fides: FidesGlobal = {
  ...initialFides,
  init,
};

updateWindowFides(_Fides);

// Export everything from ./lib/* to use when importing fides.mjs as a module
export * from "./lib/consent-context";
export * from "./lib/consent-types";
export * from "./lib/consent-utils";
export * from "./lib/consent-value";
export * from "./lib/cookie";
export * from "./lib/events";
export * from "./lib/i18n";
export * from "./lib/init-utils";
export * from "./lib/shared-consent-utils";
export * from "./services/api";
export * from "./services/external/geolocation";
