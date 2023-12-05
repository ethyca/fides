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
  ConsentMechanism,
  FidesConfig,
  FidesOptionsOverrides,
  FidesOverrides,
  GetPreferencesFnResp,
  OverrideOptions,
  PrivacyExperience,
  UserConsentPreference,
} from "./lib/consent-types";

import { generateFidesString, initializeTcfCmpApi } from "./lib/tcf";
import {
  getInitialCookie,
  getInitialFides,
  getOptionsOverrides,
  initialize,
} from "./lib/initialize";
import type { Fides } from "./lib/initialize";
import { dispatchFidesEvent } from "./lib/events";
import {
  debugLog,
  FidesCookie,
  hasSavedTcfPreferences,
  transformConsentToFidesUserPreference,
  transformTcfPreferencesToCookieKeys,
  transformUserPreferenceToBoolean,
} from "./fides";
import { renderOverlay } from "./lib/tcf/renderOverlay";
import {
  EnabledIds,
  TcfModelsRecord,
  TcfSavePreferences,
} from "./lib/tcf/types";
import { FIDES_SYSTEM_COOKIE_KEY_MAP, TCF_KEY_MAP } from "./lib/tcf/constants";
import type { GppFunction } from "./lib/gpp/types";
import { makeStub } from "./lib/tcf/stub";
import { customGetConsentPreferences } from "./services/external/preferences";
import { decodeFidesString, idsFromAcString } from "./lib/tcf/fidesString";

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

/**
 * Populates TCF entities with items from both cookie.tcf_consent and cookie.fides_string.
 * We must look at both because they contain non-overlapping info that is required for a complete TCFEntities object.
 * Returns TCF entities to be assigned to an experience.
 */
export const buildTcfEntitiesFromCookieAndFidesString = (
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

  // First update tcfEntities based on the `cookie.tcf_consent` obj
  FIDES_SYSTEM_COOKIE_KEY_MAP.forEach(({ cookieKey, experienceKey }) => {
    const cookieConsent = cookie.tcf_consent[cookieKey] ?? {};
    // @ts-ignore the array map should ensure we will get the right record type
    tcfEntities[experienceKey] = experience[experienceKey]?.map((item) => {
      const preference = Object.hasOwn(cookieConsent, item.id)
        ? transformConsentToFidesUserPreference(
            Boolean(cookieConsent[item.id]),
            ConsentMechanism.OPT_IN
          )
        : item.default_preference;
      return { ...item, current_preference: preference };
    });
  });

  // Now update tcfEntities based on the fides string
  if (cookie.fides_string) {
    const { tc: tcString, ac: acString } = decodeFidesString(
      cookie.fides_string
    );
    const acStringIds = idsFromAcString(acString);

    // Populate every field from tcModel
    const tcModel = TCString.decode(tcString);
    TCF_KEY_MAP.forEach(({ experienceKey, tcfModelKey }) => {
      const isVendorKey =
        tcfModelKey === "vendorConsents" ||
        tcfModelKey === "vendorLegitimateInterests";
      const tcIds = Array.from(tcModel[tcfModelKey])
        .filter(([, consented]) => consented)
        .map(([id]) => (isVendorKey ? `gvl.${id}` : id));
      // @ts-ignore the array map should ensure we will get the right record type
      tcfEntities[experienceKey] = experience[experienceKey]?.map((item) => {
        let consented = !!tcIds.find((id) => id === item.id);
        // Also check the AC string, which only applies to tcf_vendor_consents
        if (
          experienceKey === "tcf_vendor_consents" &&
          acStringIds.find((id) => id === item.id)
        ) {
          consented = true;
        }
        return {
          ...item,
          current_preference: transformConsentToFidesUserPreference(
            consented,
            ConsentMechanism.OPT_IN
          ),
        };
      });
    });
  }

  return tcfEntities;
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
    const tcfEntities = buildTcfEntitiesFromCookieAndFidesString(
      experience,
      cookie
    );
    return { cookie, experience: tcfEntities };
  }

  // If user has no prefs saved, we don't need to override the prefs on the cookie
  if (!hasSavedTcfPreferences(experience)) {
    return { cookie, experience };
  }

  // If the user has prefs on a client-side fetched experience, but there is no fides_string,
  // we need to use the prefs on the experience to generate
  // 1. a fidesString
  // 2. a cookie.tcf_consent (which only has system preferences since those are not captured in the fidesString)

  // 1. Generate a fidesString from the experience
  const enabledIds: EnabledIds = {
    purposesConsent: [],
    purposesLegint: [],
    specialPurposes: [],
    features: [],
    specialFeatures: [],
    vendorsConsent: [],
    vendorsLegint: [],
  };
  TCF_KEY_MAP.forEach(({ experienceKey, enabledIdsKey }) => {
    experience[experienceKey]?.forEach((record) => {
      const pref: UserConsentPreference = getInitialPreference(record);
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

  // 2. Generate a cookie object from the experience
  const tcSavePrefs: TcfSavePreferences = {};
  FIDES_SYSTEM_COOKIE_KEY_MAP.forEach(({ cookieKey, experienceKey }) => {
    tcSavePrefs[cookieKey] = [];
    experience[experienceKey]?.forEach((record) => {
      const preference = getInitialPreference(record);
      tcSavePrefs[cookieKey]?.push({ id: `${record.id}`, preference });
    });
  });
  const tcfConsent = transformTcfPreferencesToCookieKeys(tcSavePrefs);

  // Return the updated cookie
  return {
    cookie: { ...cookie, fides_string: fidesString, tcf_consent: tcfConsent },
    experience,
  };
};

/**
 * TCF version of updating prefetched experience, based on:
 * 1) experience: pre-fetched or client-side experience-based consent configuration
 * 2) cookie: cookie containing user preference.

 *
 * Returns updated experience with user preferences. We have a separate function for notices
 * and for TCF so that the bundle trees do not overlap.
 */
const updateExperienceFromCookieConsentTcf = ({
  experience,
  cookie,
  debug,
}: {
  experience: PrivacyExperience;
  cookie: FidesCookie;
  debug?: boolean;
}): PrivacyExperience => {
  const tcfEntities = buildTcfEntitiesFromCookieAndFidesString(
    experience,
    cookie
  );

  if (debug) {
    debugLog(
      debug,
      `Returning updated pre-fetched experience with user consent.`,
      experience
    );
  }
  return { ...experience, ...tcfEntities };
};

/**
 * Initialize the global Fides object with the given configuration values
 */
const init = async (config: FidesConfig) => {
  const optionsOverrides: Partial<FidesOptionsOverrides> =
    getOptionsOverrides();
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
    experience,
    renderOverlay,
    updateCookieAndExperience,
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
    gppEnabled: false,
    fidesEmbed: false,
    fidesDisableSaveApi: false,
    fidesDisableBanner: false,
    fidesString: null,
    apiOptions: null,
    fidesTcfGdprApplies: true,
    gppExtensionPath: "",
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
