/**
 * FidesJS: JavaScript SDK for Fides (https://github.com/ethyca/fides)
 *
 * This is the primary entry point for the fides.js module.
 *
 * See the overall package docs in ./docs/README.md for more!
 */
import { gtm } from "./integrations/gtm";
import { meta } from "./integrations/meta";
import { shopify } from "./integrations/shopify";

import {
  updateExperienceFromCookieConsentNotices,
  consentCookieObjHasSomeConsentSet,
} from "./lib/cookie";
import {
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
} from "./lib/consent-types";

import { dispatchFidesEvent } from "./lib/events";

import {
  initialize,
  getInitialCookie,
  getInitialFides,
  getOverridesByType,
} from "./lib/initialize";
import { renderOverlay } from "./lib/renderOverlay";
import { customGetConsentPreferences } from "./services/external/preferences";
import { defaultShowModal } from "./lib/consent-utils";
import { DEFAULT_MODAL_LINK_LABEL } from "./lib/i18n";

declare global {
  interface Window {
    Fides: FidesGlobal;
    fides_overrides: FidesOptions;
  }
}

// The global Fides object; this is bound to window.Fides if available
// eslint-disable-next-line no-underscore-dangle,@typescript-eslint/naming-convention
let _Fides: FidesGlobal;

const updateExperience = ({
  cookie,
  experience,
  debug,
  isExperienceClientSideFetched,
}: {
  cookie: FidesCookie;
  experience: PrivacyExperience;
  debug?: boolean;
  isExperienceClientSideFetched: boolean;
}): Partial<PrivacyExperience> => {
  let updatedExperience: PrivacyExperience = experience;
  const preferencesExistOnCookie = consentCookieObjHasSomeConsentSet(
    cookie.consent
  );
  if (isExperienceClientSideFetched && preferencesExistOnCookie) {
    // If we have some preferences on the cookie, we update client-side experience with those preferences
    // if the name matches. This is used for client-side UI.
    updatedExperience = updateExperienceFromCookieConsentNotices({
      experience,
      cookie,
      debug,
    });
  }
  return updatedExperience;
};

/**
 * Initialize the global Fides object with the given configuration values
 */
const init = async (config: FidesConfig) => {
  const optionsOverrides: Partial<FidesInitOptionsOverrides> =
    getOverridesByType<Partial<FidesInitOptionsOverrides>>(
      OverrideType.OPTIONS,
      config
    );
  const experienceTranslationOverrides: Partial<FidesExperienceTranslationOverrides> =
    getOverridesByType<Partial<FidesExperienceTranslationOverrides>>(
      OverrideType.EXPERIENCE_TRANSLATION,
      config
    );
  const consentPrefsOverrides: GetPreferencesFnResp | null =
    await customGetConsentPreferences(config);
  // DEFER: not implemented - ability to override notice-based consent with the consentPrefsOverrides.consent obj
  const overrides: Partial<FidesOverrides> = {
    optionsOverrides,
    consentPrefsOverrides,
    experienceTranslationOverrides,
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

  const initialFides = getInitialFides({
    ...config,
    cookie,
    savedConsent,
    updateExperienceFromCookieConsent: updateExperienceFromCookieConsentNotices,
  });
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
    overrides,
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
    tcfEnabled: false,
    fidesEmbed: false,
    fidesDisableSaveApi: false,
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
  getModalLinkLabel: () => DEFAULT_MODAL_LINK_LABEL,
};

if (typeof window !== "undefined") {
  window.Fides = _Fides;
}

// Export everything from ./lib/* to use when importing fides.mjs as a module
export * from "./services/api";
export * from "./services/external/geolocation";
export * from "./lib/consent";
export * from "./lib/consent-context";
export * from "./lib/consent-types";
export * from "./lib/consent-utils";
export * from "./lib/shared-consent-utils";
export * from "./lib/consent-value";
export * from "./lib/cookie";
export * from "./lib/events";
export * from "./lib/i18n";
