import { ContainerNode } from "preact";
import { gtm } from "../integrations/gtm";
import { meta } from "../integrations/meta";
import { shopify } from "../integrations/shopify";
import { getConsentContext } from "./consent-context";
import {
  getCookieByName,
  getOrMakeFidesCookie,
  isNewFidesCookie,
  makeConsentDefaultsLegacy,
  updateCookieFromNoticePreferences,
} from "./cookie";
import {
  ConsentMechanism,
  ConsentMethod,
  EmptyExperience,
  FidesConfig,
  FidesOptionsOverrides,
  FidesOptions,
  OverrideOptions,
  PrivacyExperience,
  SaveConsentPreference,
  UserGeolocation,
  FidesCookie,
  CookieMeta,
  CookieIdentity,
  CookieKeyConsent,
} from "./consent-types";
import {
  constructFidesRegionString,
  debugLog,
  experienceIsValid,
  getWindowObjFromPath,
  isPrivacyExperience,
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
import { setupExtensions } from "./extensions";
import {
  noticeHasConsentInCookie,
  transformConsentToFidesUserPreference,
} from "./shared-consent-utils";

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
 * Returns true if GPC has been applied
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
}): boolean => {
  if (!effectiveExperience || !effectiveExperience.privacy_notices) {
    return false;
  }

  const context = getConsentContext();
  if (!context.globalPrivacyControl) {
    return false;
  }

  let gpcApplied = false;
  const consentPreferencesToSave = effectiveExperience.privacy_notices.map(
    (notice) => {
      const hasPriorConsent = noticeHasConsentInCookie(notice, cookie);
      // only apply GPC for notices that do not have prior consent
      if (
        notice.has_gpc_flag &&
        !hasPriorConsent &&
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
          resolveConsentValue(notice, context, cookie),
          notice.consent_mechanism
        )
      );
    }
  );

  if (gpcApplied) {
    updateConsentPreferences({
      consentPreferencesToSave,
      experience: effectiveExperience,
      consentMethod: ConsentMethod.GPC,
      options: fidesOptions,
      userLocationString: fidesRegionString || undefined,
      cookie,
      updateCookie: (oldCookie) =>
        updateCookieFromNoticePreferences(oldCookie, consentPreferencesToSave),
    });
    return true;
  }
  return false;
};

/**
 * Gets and validates override options provided through URL query params, cookie, or window obj
 *
 *
 * If the same override option is provided in multiple ways, load the value in this order:
 * 1) query param  (top priority)
 * 2) window obj   (second priority)
 * 3) cookie value (last priority)
 */
export const getOptionsOverrides = (
  config: FidesConfig
): Partial<FidesOptionsOverrides> => {
  const overrideOptions: Partial<FidesOptionsOverrides> = {};
  if (typeof window !== "undefined") {
    // Grab query params if provided in the URL (e.g. "?fides_string=123...")
    const queryParams = new URLSearchParams(window.location.search);
    // Grab override options if exists (e.g. window.fides_overrides = { fides_string: "123..." })
    const customPathArr: "" | null | string[] =
      config.options.customOptionsPath &&
      config.options.customOptionsPath.split(".");
    const windowObj: OverrideOptions | undefined =
      customPathArr && customPathArr.length >= 0
        ? getWindowObjFromPath(customPathArr)
        : window.fides_overrides;

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
  return overrideOptions;
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
  updateExperienceFromCookieConsent,
}: {
  cookie: FidesCookie;
} & FidesConfig & {
    updateExperienceFromCookieConsent: (props: {
      experience: PrivacyExperience;
      cookie: FidesCookie;
      debug: boolean;
    }) => PrivacyExperience;
  }): Partial<Fides> | null => {
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
  updateExperience,
}: {
  cookie: FidesCookie;
  renderOverlay: (props: OverlayProps, parent: ContainerNode) => void;
  /**
   * Once we for sure have a valid experience, this is another chance to update values
   * before the overlay renders.
   */
  updateExperience: ({
    cookie,
    experience,
    debug,
    isExperienceClientSideFetched,
  }: {
    cookie: FidesCookie;
    experience: PrivacyExperience;
    debug?: boolean;
    isExperienceClientSideFetched: boolean;
  }) => Promise<Partial<PrivacyExperience>>;
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
        options.apiOptions
      );
    }

    if (
      isPrivacyExperience(effectiveExperience) &&
      experienceIsValid(effectiveExperience, options)
    ) {
      // apply GPC preferences
      if (shouldInitOverlay && isPrivacyExperience(effectiveExperience)) {
        automaticallyApplyGPCPreferences({
          cookie,
          fidesRegionString,
          effectiveExperience,
          fidesOptions: options,
        });
      }
      const updatedExperience = await updateExperience({
        cookie,
        experience: effectiveExperience,
        debug: options.debug,
        isExperienceClientSideFetched: fetchedClientSideExperience,
      });
      debugLog(options.debug, "Updated experience", updatedExperience);
      Object.assign(effectiveExperience, updatedExperience);
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

  // Call extensions
  // DEFER(PROD#1439): This is likely too late for the GPP stub.
  // We should move stub code out to the base package and call it right away instead.
  await setupExtensions({ options, experience: effectiveExperience });

  // return an object with the updated Fides values
  return {
    consent: cookie.consent,
    fides_meta: cookie.fides_meta,
    identity: cookie.identity,
    fides_string: cookie.fides_string,
    tcf_consent: cookie.tcf_consent,
    experience: effectiveExperience,
    geolocation,
    options,
    initialized: true,
  };
};
