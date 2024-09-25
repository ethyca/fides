import { ContainerNode } from "preact";
import { v4 as uuidv4 } from "uuid";

import { OverlayProps } from "../components/types";
import { fetchExperience } from "../services/api";
import { getGeolocation } from "../services/external/geolocation";
import { getConsentContext } from "./consent-context";
import {
  ConsentMechanism,
  ConsentMethod,
  FidesConfig,
  FidesCookie,
  FidesGlobal,
  FidesInitOptions,
  FidesOptions,
  FidesOverrides,
  NoticeConsent,
  OverrideExperienceTranslations,
  OverrideType,
  PrivacyExperience,
  SaveConsentPreference,
  UserGeolocation,
} from "./consent-types";
import {
  constructFidesRegionString,
  debugLog,
  experienceIsValid,
  getOverrideValidatorMapByType,
  getWindowObjFromPath,
  isPrivacyExperience,
  validateOptions,
} from "./consent-utils";
import { resolveConsentValue } from "./consent-value";
import {
  getCookieByName,
  getOrMakeFidesCookie,
  isNewFidesCookie,
  makeConsentDefaultsLegacy,
  updateCookieFromExperience,
  updateCookieFromNoticePreferences,
} from "./cookie";
import {
  DEFAULT_MODAL_LINK_LABEL,
  I18n,
  initializeI18n,
  localizeModalLinkText,
  selectBestExperienceConfigTranslation,
  selectBestNoticeTranslation,
  setupI18n,
} from "./i18n";
import { initOverlay } from "./initOverlay";
import { updateConsentPreferences } from "./preferences";
import {
  noticeHasConsentInCookie,
  transformConsentToFidesUserPreference,
} from "./shared-consent-utils";

export type UpdateExperienceFn = (args: {
  cookie: FidesCookie;
  experience: PrivacyExperience;
  debug?: boolean;
  isExperienceClientSideFetched: boolean;
}) => Partial<PrivacyExperience>;

const retrieveEffectiveRegionString = async (
  geolocation: UserGeolocation | undefined,
  options: FidesInitOptions,
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
        options.debug,
      ),
    );
  }
  return fidesRegionString;
};

/**
 * Opt out of notices that can be opted out of automatically.
 * This does not currently do anything with TCF.
 * Returns true if GPC has been applied
 */
const automaticallyApplyGPCPreferences = async ({
  savedConsent,
  effectiveExperience,
  cookie,
  fidesRegionString,
  fidesOptions,
  i18n,
}: {
  savedConsent: NoticeConsent;
  effectiveExperience: PrivacyExperience;
  cookie: FidesCookie;
  fidesRegionString: string | null;
  fidesOptions: FidesInitOptions;
  i18n: I18n;
}): Promise<boolean> => {
  // Early-exit if there is no experience or notices, since we've nothing to do
  if (
    !effectiveExperience ||
    !effectiveExperience.experience_config ||
    !effectiveExperience.privacy_notices ||
    effectiveExperience.privacy_notices.length === 0
  ) {
    return false;
  }

  const context = getConsentContext();
  if (!context.globalPrivacyControl) {
    return false;
  }

  /**
   * Select the "best" translation that should be used for these saved
   * preferences based on the currently active locale.
   *
   * NOTE: This *feels* a bit weird, and would feel cleaner if this was moved
   * into the UI components. However, we currently want to keep the GPC
   * application isolated, so we need to duplicate some of that "best
   * translation" logic here.
   */
  const bestTranslation = selectBestExperienceConfigTranslation(
    i18n,
    effectiveExperience.experience_config,
  );
  const privacyExperienceConfigHistoryId =
    bestTranslation?.privacy_experience_config_history_id;

  let gpcApplied = false;
  const consentPreferencesToSave = effectiveExperience.privacy_notices.map(
    (notice) => {
      const hasPriorConsent = noticeHasConsentInCookie(notice, savedConsent);
      const bestNoticeTranslation = selectBestNoticeTranslation(i18n, notice);

      // only apply GPC for notices that do not have prior consent
      if (
        notice.has_gpc_flag &&
        !hasPriorConsent &&
        notice.consent_mechanism !== ConsentMechanism.NOTICE_ONLY
      ) {
        gpcApplied = true;
        return new SaveConsentPreference(
          notice,
          transformConsentToFidesUserPreference(
            false,
            notice.consent_mechanism,
          ),
          bestNoticeTranslation?.privacy_notice_history_id,
        );
      }
      return new SaveConsentPreference(
        notice,
        transformConsentToFidesUserPreference(
          resolveConsentValue(notice, context, savedConsent),
          notice.consent_mechanism,
        ),
        bestNoticeTranslation?.privacy_notice_history_id,
      );
    },
  );

  if (gpcApplied) {
    await updateConsentPreferences({
      servedNoticeHistoryId: uuidv4(),
      consentPreferencesToSave,
      privacyExperienceConfigHistoryId,
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
 * Gets and validates overrides provided through URL query params, cookie, or window obj
 * This shared fn supports getting 2 different types of overrides: FidesOptionsOverrides and
 * FidesExperienceLanguageOverrides
 *
 * If the same override is provided in multiple ways, load the value in this order:
 * 1) query param  (top priority)
 * 2) window obj   (second priority)
 * 3) cookie value (last priority)
 */
export const getOverridesByType = <T>(
  type: OverrideType,
  config: FidesConfig,
): Partial<T> => {
  const overrides: Partial<T> = {};
  if (typeof window !== "undefined") {
    // Grab query params if provided in the URL (e.g. "?fides_string=123...")
    const queryParams = new URLSearchParams(window.location.search);
    // Grab window overrides if exists (e.g. window.fides_overrides = { fides_string: "123..." })
    const customPathArr: "" | null | string[] =
      config.options.customOptionsPath &&
      config.options.customOptionsPath.split(".");
    const windowObj:
      | Partial<FidesOptions & OverrideExperienceTranslations>
      | undefined =
      customPathArr && customPathArr.length >= 0
        ? getWindowObjFromPath(customPathArr)
        : window.fides_overrides;

    // Look for each of the override options in all three locations: query params, window object, cookie
    const overrideValidatorMap = getOverrideValidatorMapByType(type);
    overrideValidatorMap?.forEach(
      ({ overrideName, overrideType, overrideKey, validationRegex }) => {
        const queryParamOverride: string | null = queryParams.get(overrideKey);
        const windowObjOverride: string | boolean | undefined = windowObj
          ? windowObj[overrideKey]
          : undefined;
        const cookieOverride: string | undefined = getCookieByName(overrideKey);

        // Load the override value, respecting the order of precedence (query params > window object > cookie)
        const value = queryParamOverride || windowObjOverride || cookieOverride;
        if (value && validationRegex.test(value.toString())) {
          // coerce to expected type
          overrides[overrideName as keyof T] =
            overrideType === "string" ? value : JSON.parse(value.toString());
        }
      },
    );
  }
  return overrides;
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
    options.debug,
  );

  // Load any existing user preferences from the browser cookie
  return getOrMakeFidesCookie(
    consentDefaults,
    options.debug,
    options.fidesClearCookie,
  );
};

/**
 * If saved preferences are detected, immediately initialize from local cache
 */
export const getInitialFides = ({
  cookie,
  savedConsent,
  experience,
  geolocation,
  options,
  updateExperienceFromCookieConsent,
}: {
  cookie: FidesCookie;
  savedConsent: NoticeConsent;
} & FidesConfig & {
    updateExperienceFromCookieConsent: (props: {
      experience: PrivacyExperience;
      cookie: FidesCookie;
      debug: boolean;
    }) => PrivacyExperience;
  }): Partial<FidesGlobal> | null => {
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
    saved_consent: savedConsent,
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
  fides,
  options,
  geolocation,
  renderOverlay,
  updateExperience,
  overrides,
  propertyId,
}: {
  fides: FidesGlobal;
  renderOverlay: (props: OverlayProps, parent: ContainerNode) => void;
  /**
   * Once we for sure have a valid experience, this is another chance to update values
   * before the overlay renders.
   */
  updateExperience: UpdateExperienceFn;
  overrides?: Partial<FidesOverrides>;
} & FidesConfig): Promise<Partial<FidesGlobal>> => {
  let shouldInitOverlay: boolean = options.isOverlayEnabled;
  let fidesRegionString: string | null = null;
  let getModalLinkLabel: FidesGlobal["getModalLinkLabel"] = () =>
    DEFAULT_MODAL_LINK_LABEL;

  if (!fides.cookie) {
    throw new Error("Fides cookie should be initialized");
  }

  if (shouldInitOverlay) {
    if (!validateOptions(options)) {
      debugLog(
        options.debug,
        "Invalid overlay options. Skipping overlay initialization.",
        options,
      );
      shouldInitOverlay = false;
    }

    fidesRegionString = await retrieveEffectiveRegionString(
      geolocation,
      options,
    );

    let fetchedClientSideExperience = false;

    if (!fidesRegionString) {
      debugLog(
        options.debug,
        `User location could not be obtained. Skipping overlay initialization.`,
      );
      shouldInitOverlay = false;
    } else if (!isPrivacyExperience(fides.experience)) {
      fetchedClientSideExperience = true;
      // If no effective PrivacyExperience was pre-fetched, fetch one using the current region string
      // eslint-disable-next-line no-param-reassign
      fides.experience = await fetchExperience({
        userLocationString: fidesRegionString,
        fidesApiUrl: options.fidesApiUrl,
        debug: options.debug,
        apiOptions: options.apiOptions,
        requestMinimalTCF: false,
      });
    }

    if (
      isPrivacyExperience(fides.experience) &&
      experienceIsValid(fides.experience, options)
    ) {
      /**
       * Now that we've determined the effective PrivacyExperience, update it
       * with some additional client-side state so that it is initialized with
       * the user's current consent preferences, etc. and ready to display!
       */
      const updatedExperience = updateExperience({
        cookie: fides.cookie!,
        experience: fides.experience,
        debug: options.debug,
        isExperienceClientSideFetched: fetchedClientSideExperience,
      });
      debugLog(
        options.debug,
        "Updated experience from saved preferences",
        updatedExperience,
      );
      // eslint-disable-next-line no-param-reassign
      fides.experience = { ...fides.experience, ...updatedExperience };

      /**
       * Finally, update the "cookie" state to track the user's *current*
       * consent preferences as determined by the updatedExperience above. This
       * "cookie" state is then published to external listeners via the
       * Fides.consent object and Fides events like FidesInitialized below, so
       * we rely on keeping it up to date!
       *
       * DEFER (PROD-1780): This is quite *literally* duplicate state, and means
       * we end up with three potential sources of consent preferences:
       * 1. "savedConsent": user's *saved* consent from the fides_consent cookie
       * 2. "experience.privacy_notices[].current_preference": user's current/unsaved preferences shown in the UI
       * 3. "cookie": another version of user's current/unsaved preferences
       *
       * Simplifying this state management helps us simplify FidesJS, but it's
       * tricky to do without accidentally breaking something, so be careful!
       */
      const updatedCookie = updateCookieFromExperience({
        cookie: fides.cookie,
        experience: fides.experience,
      });
      debugLog(
        options.debug,
        "Updated current cookie state from experience",
        updatedCookie,
      );
      // eslint-disable-next-line no-param-reassign
      fides.cookie = updatedCookie;

      if (shouldInitOverlay) {
        // Initialize the i18n singleton before we render the overlay
        const i18n = setupI18n();
        initializeI18n(
          i18n,
          window?.navigator,
          fides.experience,
          options,
          overrides?.experienceTranslationOverrides,
        );

        // Provide the modal link label function to the client based on the current locale unless specified via props.
        getModalLinkLabel = (props) =>
          localizeModalLinkText(
            !!props?.disableLocalization,
            i18n,
            fides.experience,
          );

        // OK, we're (finally) ready to initialize & render the overlay!
        initOverlay({
          options,
          experience: fides.experience,
          i18n,
          fidesRegionString: fidesRegionString as string,
          cookie: fides.cookie,
          savedConsent: fides.saved_consent,
          renderOverlay,
          propertyId,
          translationOverrides: overrides?.experienceTranslationOverrides,
        }).catch((e) => {
          debugLog(options.debug, e);
        });

        /**
         * Last up: apply GPC to the current preferences automatically. This will
         * set any applicable notices to "opt-out" unless the user has previously
         * saved consent, etc.
         *
         * NOTE: We want to finish initialization immediately while GPC updates
         * continue to run in the background. To ensure that any GPC API calls
         * don't block the rest of the code from executing, we use setTimeout with
         * no delay which simply moves it to the end of the JavaScript event queue.
         */
        setTimeout(
          automaticallyApplyGPCPreferences.bind(null, {
            savedConsent: fides.saved_consent,
            effectiveExperience: fides.experience as PrivacyExperience,
            cookie: fides.cookie,
            fidesRegionString,
            fidesOptions: options,
            i18n,
          }),
        );
      }
    }
  }

  // eslint-disable-next-line @typescript-eslint/naming-convention
  const { consent, fides_meta, identity, fides_string, tcf_consent } =
    fides.cookie;

  // return an object with the updated Fides values
  return {
    consent,
    fides_meta,
    identity,
    fides_string,
    tcf_consent,
    experience: fides.experience,
    geolocation,
    options,
    initialized: true,
    getModalLinkLabel,
  };
};
