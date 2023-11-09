import { ContainerNode } from "preact";
import { gtm } from "../integrations/gtm";
import { meta } from "../integrations/meta";
import { shopify } from "../integrations/shopify";
import { getConsentContext } from "./consent-context";
import {
  CookieIdentity,
  CookieKeyConsent,
  CookieMeta,
  FidesCookie,
  getCookieByName,
  getOrMakeFidesCookie,
  isNewFidesCookie,
  makeConsentDefaultsLegacy,
  updateCookieFromNoticePreferences,
  updateExperienceFromCookieConsent,
} from "./cookie";
import {
  ConsentMechanism,
  ConsentMethod,
  EmptyExperience,
  FidesConfig,
  FidesOptionOverrides,
  FidesOptions,
  FidesOverrides,
  GetPreferencesFnResp,
  PrivacyExperience,
  SaveConsentPreference,
  UserGeolocation,
} from "./consent-types";
import {
  constructFidesRegionString,
  debugLog,
  experienceIsValid,
  isPrivacyExperience,
  transformConsentToFidesUserPreference,
  validateOptions,
} from "./consent-utils";
import { fetchExperience } from "../services/api";
import { getGeolocation } from "../services/external/geolocation";
import { OverlayProps } from "../components/types";
import { updateConsentPreferences } from "./preferences";
import { resolveConsentValue } from "./consent-value";
import { initOverlay } from "./consent";
import { TcfCookieConsent } from "./tcf/types";
import { FIDES_OVERRIDE_OPTIONS_VALIDATOR_MAP } from "./consent-constants";
import { customGetConsentPreferences } from "../services/external/preferences";

export type Fides = {
  consent: CookieKeyConsent;
  experience?: PrivacyExperience | EmptyExperience;
  geolocation?: UserGeolocation;
  fides_string?: string | undefined;
  options: FidesOptions;
  fides_meta: CookieMeta;
  tcf_consent: TcfCookieConsent;
  gtm: typeof gtm;
  identity: CookieIdentity;
  init: (config: FidesConfig) => Promise<void>;
  initialized: boolean;
  meta: typeof meta;
  shopify: typeof shopify;
};

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

/**
 * Opt out of notices that can be opted out of automatically.
 * This does not currently do anything with TCF.
 */
const automaticallyApplyGPCPreferences = ({
  cookie,
  fidesRegionString,
  effectiveExperience,
  fidesOptions,
}: {
  cookie: FidesCookie;
  fidesRegionString: string | null;
  effectiveExperience?: PrivacyExperience;
  fidesOptions: FidesOptions;
}) => {
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
      experience: effectiveExperience,
      consentMethod: ConsentMethod.gpc,
      options: fidesOptions,
      userLocationString: fidesRegionString || undefined,
      cookie,
      updateCookie: (oldCookie) =>
        updateCookieFromNoticePreferences(oldCookie, consentPreferencesToSave),
    });
  }
};

/**
 * Gets and validates override options provided through URL query params, cookie, or window obj,
 * and optionally retrieves consent preference overrides if a custom fn was defined in the config.
 *
 *
 * If the same override option is provided in multiple ways, load the value in this order:
 * 1) query param  (top priority)
 * 2) window obj   (second priority)
 * 3) cookie value (last priority)
 */
export const getOverrides = async (
  config: FidesConfig
): Promise<Partial<FidesOverrides>> => {
  const overrideOptions: Partial<FidesOptionOverrides> = {};
  if (typeof window !== "undefined") {
    // Grab query params if provided in the URL (e.g. "?fides_string=123...")
    const queryParams = new URLSearchParams(window.location.search);
    // Grab global window object if provided (e.g. window.config.tc_info = { fides_string: "123..." })
    // DEFER (PROD-1243): support a configurable "custom options" path
    const windowObj = window.config?.tc_info;

    // Look for each of the override options in all three locations: query params, window object, cookie
    FIDES_OVERRIDE_OPTIONS_VALIDATOR_MAP.forEach(
      ({ fidesOption, fidesOptionType, fidesOverrideKey, validationRegex }) => {
        const queryParamOverride: string | null =
          queryParams.get(fidesOverrideKey);
        const windowObjOverride: string | boolean | undefined = windowObj
          ? windowObj[fidesOverrideKey]
          : undefined;
        const cookieOverride: string | undefined =
          getCookieByName(fidesOverrideKey);

        // Load the override option value, respecting the order of precedence (query params > window object > cookie)
        const value = queryParamOverride || windowObjOverride || cookieOverride;
        if (value && validationRegex.test(value.toString())) {
          // coerce to expected type in FidesOptions
          overrideOptions[fidesOption] =
            fidesOptionType === "string" ? value : JSON.parse(value.toString());
        }
      }
    );
  }
  const overrideConsentPrefs: GetPreferencesFnResp | null =
    await customGetConsentPreferences(config);
  if (!overrideOptions.fidesString && overrideConsentPrefs?.fides_string) {
    overrideOptions.fidesString = overrideConsentPrefs.fides_string;
  }
  return { overrideOptions, overrideConsentPrefs };
};

/**
 * Get the initial Fides cookie based on legacy consent values
 * as well as any preferences stored in existing cookies
 */
export const getInitialCookie = ({ consent, options }: FidesConfig) => {
  // Configure the default legacy consent values
  const context = getConsentContext();
  const consentDefaults = makeConsentDefaultsLegacy(
    consent,
    context,
    options.debug
  );

  // Load any existing user preferences from the browser cookie
  return getOrMakeFidesCookie(consentDefaults, options.debug);
};

/**
 * If saved preferences are detected, immediately initialize from local cache
 */
export const getInitialFides = ({
  cookie,
  experience,
  geolocation,
  options,
}: {
  cookie: FidesCookie;
} & FidesConfig): Partial<Fides> | null => {
  const hasExistingCookie = !isNewFidesCookie(cookie);
  if (!hasExistingCookie && !options.fidesString) {
    // A TC str can be injected and take effect even if the user has no previous Fides Cookie
    return null;
  }
  let updatedExperience = experience;
  if (isPrivacyExperience(experience)) {
    // at this point, pre-fetched experience contains no user consent, so we populate with the Fides cookie
    updatedExperience = updateExperienceFromCookieConsent({
      experience,
      cookie,
      debug: options.debug,
    });
  }

  return {
    consent: cookie.consent,
    fides_meta: cookie.fides_meta,
    identity: cookie.identity,
    experience: updatedExperience,
    tcf_consent: cookie.tcf_consent,
    fides_string: cookie.fides_string,
    geolocation,
    options,
    initialized: true,
  };
};

/**
 * The bulk of the initialization logic
 * 1. Validates options
 * 2. Retrieves geolocation
 * 3. Retrieves experience
 * 4. Updates cookie
 * 5. Initialize overlay components
 * 6. Apply GPC if necessary
 */
export const initialize = async ({
  cookie,
  options,
  experience,
  geolocation,
  renderOverlay,
  updateCookieAndExperience,
}: {
  cookie: FidesCookie;
  renderOverlay: (props: OverlayProps, parent: ContainerNode) => void;
  /**
   * Once we for sure have a valid experience, this is another chance to update values
   * before the overlay renders.
   */
  updateCookieAndExperience: ({
    cookie,
    experience,
    debug,
    isExperienceClientSideFetched,
  }: {
    cookie: FidesCookie;
    experience: PrivacyExperience;
    debug?: boolean;
    isExperienceClientSideFetched: boolean;
  }) => Promise<{
    cookie: FidesCookie;
    experience: Partial<PrivacyExperience>;
  }>;
} & FidesConfig): Promise<Partial<Fides>> => {
  let shouldInitOverlay: boolean = options.isOverlayEnabled;
  let effectiveExperience = experience;
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

    let fetchedClientSideExperience = false;

    if (!fidesRegionString) {
      debugLog(
        options.debug,
        `User location could not be obtained. Skipping overlay initialization.`
      );
      shouldInitOverlay = false;
    } else if (!isPrivacyExperience(effectiveExperience)) {
      fetchedClientSideExperience = true;
      // If no effective PrivacyExperience was pre-fetched, fetch one using the current region string
      effectiveExperience = await fetchExperience(
        fidesRegionString,
        options.fidesApiUrl,
        options.debug,
        options.apiOptions,
        cookie.identity.fides_user_device_id
      );
    }

    if (
      isPrivacyExperience(effectiveExperience) &&
      experienceIsValid(effectiveExperience, options)
    ) {
      const updated = await updateCookieAndExperience({
        cookie,
        experience: effectiveExperience,
        debug: options.debug,
        isExperienceClientSideFetched: fetchedClientSideExperience,
      });
      debugLog(options.debug, "Updated cookie and experience", updated);
      Object.assign(cookie, updated.cookie);
      Object.assign(effectiveExperience, updated.experience);
      if (shouldInitOverlay) {
        await initOverlay({
          experience: effectiveExperience,
          fidesRegionString: fidesRegionString as string,
          cookie,
          options,
          renderOverlay,
        }).catch(() => {});
      }
    }
  }
  if (shouldInitOverlay && isPrivacyExperience(effectiveExperience)) {
    automaticallyApplyGPCPreferences({
      cookie,
      fidesRegionString,
      effectiveExperience,
      fidesOptions: options,
    });
  }

  // return an object with the updated Fides values
  return {
    consent: cookie.consent,
    fides_meta: cookie.fides_meta,
    identity: cookie.identity,
    fides_string: cookie.fides_string,
    tcf_consent: cookie.tcf_consent,
    experience,
    geolocation,
    options,
    initialized: true,
  };
};
