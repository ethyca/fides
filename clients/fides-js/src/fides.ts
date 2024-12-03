/**
 * FidesJS: JavaScript SDK for Fides (https://github.com/ethyca/fides)
 *
 * This is the primary entry point for the fides.js module.
 *
 * See the overall package docs in ./docs/README.md for more!
 */
import { blueconic } from "./integrations/blueconic";
import { gtm } from "./integrations/gtm";
import { meta } from "./integrations/meta";
import { shopify } from "./integrations/shopify";
import { raise } from "./lib/common-utils";
import {
  ConsentMethod,
  FidesConfig,
  FidesExperienceTranslationOverrides,
  FidesGlobal,
  FidesInitOptionsOverrides,
  FidesOptions,
  FidesOverrides,
  GetPreferencesFnResp,
  OverrideType,
  PrivacyExperience,
} from "./lib/consent-types";
import {
  defaultShowModal,
  isPrivacyExperience,
  shouldResurfaceConsent,
} from "./lib/consent-utils";
import {
  consentCookieObjHasSomeConsentSet,
  updateExperienceFromCookieConsentNotices,
} from "./lib/cookie";
import { initializeDebugger } from "./lib/debugger";
import { dispatchFidesEvent, onFidesEvent } from "./lib/events";
import { DEFAULT_MODAL_LINK_LABEL } from "./lib/i18n";
import {
  getInitialCookie,
  getInitialFides,
  getOverridesByType,
  initialize,
  UpdateExperienceFn,
} from "./lib/initialize";
import { renderOverlay } from "./lib/renderOverlay";
import { customGetConsentPreferences } from "./services/external/preferences";

declare global {
  interface Window {
    Fides: FidesGlobal;
    fides_overrides: FidesOptions;
    fidesDebugger: (...args: unknown[]) => void;
  }
}

const updateWindowFides = (fidesGlobal: FidesGlobal) => {
  if (typeof window !== "undefined") {
    window.Fides = fidesGlobal;
  }
};

const updateExperience: UpdateExperienceFn = ({
  cookie,
  experience,
  isExperienceClientSideFetched,
}): Partial<PrivacyExperience> => {
  let updatedExperience: PrivacyExperience = experience;
  const preferencesExistOnCookie = consentCookieObjHasSomeConsentSet(
    cookie.consent,
  );
  if (isExperienceClientSideFetched && preferencesExistOnCookie) {
    // If we have some preferences on the cookie, we update client-side experience with those preferences
    // if the name matches. This is used for client-side UI.
    updatedExperience = updateExperienceFromCookieConsentNotices({
      experience,
      cookie,
    });
  }
  return updatedExperience;
};

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

  dispatchFidesEvent(
    "FidesInitializing",
    undefined,
    this.config.options.debug,
    {
      gppEnabled:
        this.config.options.gppEnabled ||
        this.config.experience?.gpp_settings?.enabled,
      tcfEnabled: this.config.options.tcfEnabled,
    },
  );

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
  const consentPrefsOverrides: GetPreferencesFnResp | null =
    await customGetConsentPreferences(config);
  // DEFER: not implemented - ability to override notice-based consent with the consentPrefsOverrides.consent obj
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
    ...overrides.consentPrefsOverrides?.consent,
  };

  // Keep a copy of saved consent from the cookie, since we update the "cookie"
  // value during initialization based on overrides, experience, etc.
  this.saved_consent = {
    ...this.cookie.consent,
  };

  const initialFides = getInitialFides({
    ...config,
    cookie: this.cookie,
    savedConsent: this.saved_consent,
    updateExperienceFromCookieConsent: updateExperienceFromCookieConsentNotices,
  });
  if (initialFides) {
    Object.assign(this, initialFides);
    updateWindowFides(this);
    dispatchFidesEvent("FidesInitialized", this.cookie, config.options.debug, {
      shouldShowExperience: this.shouldShowExperience(),
    });
  }
  this.experience = initialFides?.experience ?? config.experience;
  const updatedFides = await initialize({
    ...config,
    fides: this,
    renderOverlay,
    updateExperience,
    overrides,
    propertyId: config.propertyId,
  });
  Object.assign(this, updatedFides);
  updateWindowFides(this);
  // Dispatch the "FidesInitialized" event to update listeners with the initial state.
  dispatchFidesEvent("FidesInitialized", this.cookie, config.options.debug, {
    shouldShowExperience: this.shouldShowExperience(),
  });
}

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
    tcfEnabled: false,
    gppEnabled: false,
    fidesEmbed: false,
    fidesDisableSaveApi: false,
    fidesDisableNoticesServedApi: false,
    fidesDisableBanner: false,
    fidesString: null,
    apiOptions: null,
    fidesTcfGdprApplies: false,
    fidesJsBaseUrl: "",
    customOptionsPath: null,
    preventDismissal: false,
    allowHTMLDescription: null,
    base64Cookie: false,
    fidesPrimaryColor: null,
    fidesClearCookie: false,
    showFidesBrandLink: true,
    fidesConsentOverride: null,
  },
  fides_meta: {},
  identity: {},
  tcf_consent: {},
  saved_consent: {},
  blueconic,
  gtm,
  init,
  config: undefined,
  reinitialize() {
    if (!this.config || !this.initialized) {
      throw new Error("Fides must be initialized before reinitializing");
    }
    return this.init();
  },
  initialized: false,
  onFidesEvent,
  shouldShowExperience() {
    if (!isPrivacyExperience(this.experience)) {
      // Nothing to show if there's no experience
      return false;
    }
    if (
      this.options.fidesConsentOverride === ConsentMethod.ACCEPT ||
      this.options.fidesConsentOverride === ConsentMethod.REJECT
    ) {
      // If consent preference was automatic, we should not show the experience
      return false;
    }
    if (!this.cookie) {
      throw new Error("Should have a cookie");
    }
    return shouldResurfaceConsent(
      this.experience,
      this.cookie,
      this.saved_consent,
    );
  },
  meta,
  shopify,
  showModal: defaultShowModal,
  getModalLinkLabel: () => DEFAULT_MODAL_LINK_LABEL,
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
export * from "./lib/initOverlay";
export * from "./lib/shared-consent-utils";
export * from "./services/api";
export * from "./services/external/geolocation";
