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
  readConsentFromAnyProvider,
  registerDefaultProviders,
} from "./lib/consent-migration";
import {
  ConsentMethod,
  FidesConfig,
  FidesCookie,
  FidesExperienceTranslationOverrides,
  FidesGlobal,
  FidesInitOptionsOverrides,
  FidesOptions,
  FidesOverrides,
  GetPreferencesFnResp,
  NoticeConsent,
  OverrideType,
  PrivacyExperience,
  SaveConsentPreference,
  UserConsentPreference,
} from "./lib/consent-types";
import {
  decodeNoticeConsentString,
  defaultShowModal,
  encodeNoticeConsentString,
  isPrivacyExperience,
  shouldResurfaceBanner,
} from "./lib/consent-utils";
import {
  consentCookieObjHasSomeConsentSet,
  getFidesConsentCookie,
  saveFidesCookie,
  updateExperienceFromCookieConsentNotices,
} from "./lib/cookie";
import { initializeDebugger } from "./lib/debugger";
import { dispatchFidesEvent, onFidesEvent } from "./lib/events";
import { DecodedFidesString, decodeFidesString } from "./lib/fides-string";
import { DEFAULT_LOCALE, DEFAULT_MODAL_LINK_LABEL } from "./lib/i18n";
import {
  getInitialCookie,
  getInitialFides,
  getOverridesByType,
  initialize,
  UpdateExperienceFn,
} from "./lib/initialize";
import { initOverlay } from "./lib/initOverlay";
import { updateConsentPreferences } from "./lib/preferences";
import { renderOverlay } from "./lib/renderOverlay";
import {
  transformConsentToFidesUserPreference,
  transformUserPreferenceToBoolean,
} from "./lib/shared-consent-utils";
import { customGetConsentPreferences } from "./services/external/preferences";

declare global {
  interface Window {
    Fides: FidesGlobal;
    fides_overrides: Partial<FidesOptions>;
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
}): Partial<PrivacyExperience> => {
  let updatedExperience: PrivacyExperience = experience;
  const preferencesExistOnCookie = consentCookieObjHasSomeConsentSet(
    cookie.consent,
  );
  if (preferencesExistOnCookie) {
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
  // if we don't already have a fidesString override, use fidesString from consent prefs if they exist
  if (!optionsOverrides.fidesString && consentPrefsOverrides?.fides_string) {
    optionsOverrides.fidesString = consentPrefsOverrides.fides_string;
  }
  const overrides: Partial<FidesOverrides> = {
    optionsOverrides,
    consentPrefsOverrides,
    experienceTranslationOverrides,
  };

  // Register any configured consent migration providers
  registerDefaultProviders(optionsOverrides);

  // Check for migrated consent from any registered providers
  let migratedConsent: NoticeConsent | undefined;
  let hasMigratedConsent = false;
  let migrationMethod: ConsentMethod | undefined;

  if (!getFidesConsentCookie()) {
    const { consent, method } = readConsentFromAnyProvider(optionsOverrides);
    if (consent && method) {
      migratedConsent = consent;
      migrationMethod = method;
    }
  }

  config = {
    ...config,
    options: { ...config.options, ...overrides.optionsOverrides },
  };
  this.cookie = getInitialCookie(config);
  this.cookie.consent = {
    ...this.cookie.consent,
    ...migratedConsent,
  };

  // Keep a copy of saved consent from the cookie, since we update the "cookie"
  // value during initialization based on overrides, experience, etc.
  this.saved_consent = {
    ...this.cookie.consent,
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

  if (migratedConsent && migrationMethod) {
    // If we have migrated consent, we need to write the cookie to the browser
    Object.assign(this.cookie.fides_meta, {
      consentMethod: migrationMethod,
    });
    fidesDebugger("Saving migrated preferences to Fides cookie");
    saveFidesCookie(this.cookie, config.options.base64Cookie);
    hasMigratedConsent = true;
  }

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
    initOverlay,
    renderOverlay,
    updateExperience,
    overrides,
    propertyId: config.propertyId,
  });
  Object.assign(this, updatedFides);
  updateWindowFides(this);

  // Now that we have the final experience, we can save migrated preferences to the API, if they exist
  if (
    migratedConsent &&
    hasMigratedConsent &&
    migrationMethod &&
    isPrivacyExperience(this.experience) &&
    this.experience.privacy_notices
  ) {
    const noticeMap = new Map(
      this.experience.privacy_notices.map((notice) => [
        notice.notice_key,
        notice,
      ]),
    );
    const consentPreferencesToSave = Object.entries(this.cookie.consent)
      .map(([key, value]) => {
        const notice = noticeMap.get(key);
        if (!notice) {
          return null;
        }
        if (typeof value === "string") {
          // eslint-disable-next-line no-param-reassign
          value = transformUserPreferenceToBoolean(
            value as UserConsentPreference,
          );
        }
        return new SaveConsentPreference(
          notice,
          transformConsentToFidesUserPreference(value),
          key,
        );
      })
      .filter((pref): pref is SaveConsentPreference => pref !== null);

    await updateConsentPreferences({
      consentPreferencesToSave,
      experience: this.experience as PrivacyExperience,
      consentMethod: migrationMethod,
      options: config.options,
      cookie: this.cookie,
      userLocationString: this.geolocation?.region,
      updateCookie: async (oldCookie) => {
        // Just return the current cookie since we've already updated it
        return oldCookie;
      },
      propertyId: config.propertyId,
    });
  }

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
  locale: DEFAULT_LOCALE,
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
    otFidesMapping: null,
    fidesDisabledNotices: null,
    fidesConsentNonApplicableFlagMode: null,
    fidesConsentFlagType: null,
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
    return shouldResurfaceBanner(
      this.experience,
      this.cookie,
      this.saved_consent,
      this.options,
    );
  },
  meta,
  shopify,
  showModal: defaultShowModal,
  getModalLinkLabel: () => DEFAULT_MODAL_LINK_LABEL,
  encodeNoticeConsentString,
  decodeNoticeConsentString,
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
