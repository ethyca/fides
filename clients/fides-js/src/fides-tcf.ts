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
import { getConsentContext } from "./lib/consent-context";
import { initOverlay } from "./lib/consent";
import {
  CookieKeyConsent,
  CookieIdentity,
  CookieMeta,
  getOrMakeFidesCookie,
  makeConsentDefaultsLegacy,
  buildCookieConsentForExperiences,
  FidesCookie,
  isNewFidesCookie,
} from "./lib/cookie";
import {
  PrivacyExperience,
  FidesConfig,
  FidesOptions,
  UserGeolocation,
  ConsentMethod,
  SaveConsentPreference,
  ConsentMechanism,
} from "./lib/consent-types";
import {
  constructFidesRegionString,
  debugLog,
  experienceIsValid,
  transformConsentToFidesUserPreference,
  validateOptions,
} from "./lib/consent-utils";
import { dispatchFidesEvent } from "./lib/events";
import { fetchExperience } from "./services/fides/api";
import { getGeolocation } from "./services/external/geolocation";
import { OverlayProps } from "./components/Overlay";
import { updateConsentPreferences } from "./lib/preferences";
import { resolveConsentValue } from "./lib/consent-value";
import { load_tcf } from "./lib/tcf";

export type Fides = {
  consent: CookieKeyConsent;
  experience?: PrivacyExperience;
  geolocation?: UserGeolocation;
  options: FidesOptions;
  fides_meta: CookieMeta;
  gtm: typeof gtm;
  identity: CookieIdentity;
  init: typeof init;
  initialized: boolean;
  meta: typeof meta;
  shopify: typeof shopify;
};

declare global {
  interface Window {
    Fides: Fides;
  }
}

// The global Fides object; this is bound to window.Fides if available
// eslint-disable-next-line no-underscore-dangle,@typescript-eslint/naming-convention
let _Fides: Fides;

const retrieveEffectiveRegionString = async (
  geolocation: UserGeolocation | undefined,
  options: FidesOptions
) => {
  // Prefer the provided geolocation if available and valid; otherwise, fallback to automatically
  // geolocating the user by calling the geolocation API
  const fidesRegionString = constructFidesRegionString(geolocation);
  if (!fidesRegionString) {
    // we always need a region str so that we can PATCH privacy preferences to Fides Api
    return constructFidesRegionString(
      // Call the geolocation API
      await getGeolocation(
        options.isGeolocationEnabled,
        options.geolocationApiUrl,
        options.debug
      )
    );
  }
  return fidesRegionString;
};

const automaticallyApplyGPCPreferences = (
  cookie: FidesCookie,
  fidesRegionString: string | null,
  fidesApiUrl: string,
  effectiveExperience?: PrivacyExperience | null
) => {
  if (!effectiveExperience || !effectiveExperience.privacy_notices) {
    return;
  }

  const context = getConsentContext();
  if (!context.globalPrivacyControl) {
    return;
  }

  let gpcApplied = false;
  const consentPreferencesToSave = effectiveExperience.privacy_notices.map(
    (notice) => {
      if (
        notice.has_gpc_flag &&
        !notice.current_preference &&
        notice.consent_mechanism !== ConsentMechanism.NOTICE_ONLY
      ) {
        gpcApplied = true;
        return new SaveConsentPreference(
          notice,
          transformConsentToFidesUserPreference(false, notice.consent_mechanism)
        );
      }
      return new SaveConsentPreference(
        notice,
        transformConsentToFidesUserPreference(
          resolveConsentValue(notice, context),
          notice.consent_mechanism
        )
      );
    }
  );

  if (gpcApplied) {
    updateConsentPreferences({
      consentPreferencesToSave,
      experienceId: effectiveExperience.id,
      fidesApiUrl,
      consentMethod: ConsentMethod.gpc,
      userLocationString: fidesRegionString || undefined,
      cookie,
    });
  }
};

/**
 * Initialize the global Fides object with the given configuration values
 */
export const init = async ({
  consent,
  experience,
  geolocation,
  options,
}: FidesConfig) => {
  load_tcf();

  // Configure the default legacy consent values
  const context = getConsentContext();
  const consentDefaults = makeConsentDefaultsLegacy(
    consent,
    context,
    options.debug
  );

  // Load any existing user preferences from the browser cookie
  const cookie: FidesCookie = getOrMakeFidesCookie(
    consentDefaults,
    options.debug
  );

  // If saved preferences are detected, immediately initialize from local cache,
  // and then continue geolocating, etc.
  const hasExistingCookie = !isNewFidesCookie(cookie);
  if (hasExistingCookie) {
    _Fides.consent = cookie.consent;
    _Fides.fides_meta = cookie.fides_meta;
    _Fides.identity = cookie.identity;
    _Fides.experience = experience;
    _Fides.geolocation = geolocation;
    _Fides.options = options;
    _Fides.initialized = true;
    dispatchFidesEvent("FidesInitialized", cookie, options.debug);
    dispatchFidesEvent("FidesUpdated", cookie, options.debug);
  }

  let shouldInitOverlay: boolean = options.isOverlayEnabled;
  let effectiveExperience: PrivacyExperience | undefined | null = experience;
  let fidesRegionString: string | null = null;

  if (shouldInitOverlay) {
    if (!validateOptions(options)) {
      debugLog(
        options.debug,
        "Invalid overlay options. Skipping overlay initialization.",
        options
      );
      shouldInitOverlay = false;
    }

    fidesRegionString = await retrieveEffectiveRegionString(
      geolocation,
      options
    );

    if (!fidesRegionString) {
      debugLog(
        options.debug,
        `User location could not be obtained. Skipping overlay initialization.`
      );
      shouldInitOverlay = false;
    } else if (!effectiveExperience) {
      effectiveExperience = await fetchExperience(
        fidesRegionString,
        options.fidesApiUrl,
        cookie.identity.fides_user_device_id,
        options.debug
      );
    }

    if (
      effectiveExperience &&
      experienceIsValid(effectiveExperience, options)
    ) {
      // Overwrite cookie consent with experience-based consent values
      cookie.consent = buildCookieConsentForExperiences(
        effectiveExperience,
        context,
        options.debug
      );

      if (shouldInitOverlay) {
        await initOverlay(<OverlayProps>{
          experience: effectiveExperience,
          fidesRegionString,
          cookie,
          options,
        }).catch(() => {});
      }
    }
  }
  if (shouldInitOverlay) {
    automaticallyApplyGPCPreferences(
      cookie,
      fidesRegionString,
      options.fidesApiUrl,
      effectiveExperience
    );
  }

  // Initialize the window.Fides object
  _Fides.consent = cookie.consent;
  _Fides.fides_meta = cookie.fides_meta;
  _Fides.identity = cookie.identity;
  _Fides.experience = experience;
  _Fides.geolocation = geolocation;
  _Fides.options = options;
  _Fides.initialized = true;

  // Dispatch the "FidesInitialized" event to update listeners with the initial
  // state. Skip if we already initialized due to an existing cookie.
  // For convenience, also dispatch the "FidesUpdated" event; this allows
  // listeners to ignore the initialization event if they prefer
  if (!hasExistingCookie) {
    dispatchFidesEvent("FidesInitialized", cookie, options.debug);
  }
  dispatchFidesEvent("FidesUpdated", cookie, options.debug);
};

// The global Fides object; this is bound to window.Fides if available
_Fides = {
  consent: {},
  experience: undefined,
  geolocation: {},
  options: {
    debug: true,
    isOverlayEnabled: false,
    isGeolocationEnabled: false,
    geolocationApiUrl: "",
    overlayParentId: null,
    modalLinkId: null,
    privacyCenterUrl: "",
    fidesApiUrl: "",
    tcfEnabled: true,
  },
  fides_meta: {},
  identity: {},
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
export * from "./lib/consent";
export * from "./lib/consent-context";
export * from "./lib/consent-types";
export * from "./lib/consent-utils";
export * from "./lib/consent-value";
export * from "./lib/cookie";
export * from "./lib/events";

// DEFER: this default export isn't very useful, it's just the Fides type
export default Fides;
