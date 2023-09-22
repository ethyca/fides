import { ContainerNode } from "preact";
import { gtm } from "../integrations/gtm";
import { meta } from "../integrations/meta";
import { shopify } from "../integrations/shopify";
import { getConsentContext } from "./consent-context";
import {
  buildCookieConsentForExperiences,
  CookieIdentity,
  CookieKeyConsent,
  CookieMeta,
  FidesCookie,
  getOrMakeFidesCookie,
  isNewFidesCookie,
  makeConsentDefaultsLegacy,
  updateExperienceFromCookieConsent,
} from "./cookie";
import {
  ConsentMechanism,
  ConsentMethod,
  EmptyExperience,
  FidesConfig,
  FidesOptions,
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
import { fetchExperience } from "../services/fides/api";
import { getGeolocation } from "../services/external/geolocation";
import { OverlayProps } from "../components/types";
import { updateConsentPreferences } from "./preferences";
import { resolveConsentValue } from "./consent-value";
import { initOverlay } from "./consent";

export type Fides = {
  consent: CookieKeyConsent;
  experience?: PrivacyExperience | EmptyExperience;
  geolocation?: UserGeolocation;
  tcString?: string | undefined;
  options: FidesOptions;
  fides_meta: CookieMeta;
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

const automaticallyApplyGPCPreferences = (
  cookie: FidesCookie,
  fidesRegionString: string | null,
  fidesApiUrl: string,
  effectiveExperience?: PrivacyExperience
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
  const cookie: FidesCookie = getOrMakeFidesCookie(
    consentDefaults,
    options.debug
  );
  return cookie;
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
  if (!hasExistingCookie) {
    return null;
  }

  let updatedExperience = experience;
  if (isPrivacyExperience(experience)) {
    // at this point, pre-fetched experience contains no user consent, so we populate with the Fides cookie
    updatedExperience = updateExperienceFromCookieConsent(
      experience,
      cookie,
      options.debug
    );
  }

  return {
    consent: cookie.consent,
    fides_meta: cookie.fides_meta,
    identity: cookie.identity,
    experience: updatedExperience,
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
  updateCookie,
}: {
  cookie: FidesCookie;
  renderOverlay: (props: OverlayProps, parent: ContainerNode) => void;
  updateCookie?: (
    oldCookie: FidesCookie,
    experience: PrivacyExperience
  ) => Promise<FidesCookie>;
} & FidesConfig): Promise<Partial<Fides>> => {
  const context = getConsentContext();

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

    if (!fidesRegionString) {
      debugLog(
        options.debug,
        `User location could not be obtained. Skipping overlay initialization.`
      );
      shouldInitOverlay = false;
      // An empty experience (e.g. {}) is expected when 1. pre-fetch is enabled, and 2. the location has no associated
      // experience. We should not fetch experiences again in this case. We only fetch experiences if it's undefined.
    } else if (!experience) {
      effectiveExperience = await fetchExperience(
        fidesRegionString,
        options.fidesApiUrl,
        options.debug,
        cookie.identity.fides_user_device_id
      );
    }

    if (
      isPrivacyExperience(effectiveExperience) &&
      experienceIsValid(effectiveExperience, options)
    ) {
      // Overwrite cookie consent with experience-based consent values
      // eslint-disable-next-line no-param-reassign
      cookie.consent = buildCookieConsentForExperiences(
        effectiveExperience,
        context,
        options.debug
      );

      if (updateCookie) {
        // eslint-disable-next-line no-param-reassign
        cookie = await updateCookie(cookie, effectiveExperience);
      }

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
    automaticallyApplyGPCPreferences(
      cookie,
      fidesRegionString,
      options.fidesApiUrl,
      effectiveExperience
    );
  }

  // return an object with the updated Fides values
  return {
    consent: cookie.consent,
    fides_meta: cookie.fides_meta,
    identity: cookie.identity,
    tcString: cookie.tcString,
    experience,
    geolocation,
    options,
    initialized: true,
  };
};
