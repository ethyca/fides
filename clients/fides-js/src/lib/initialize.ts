import { ContainerNode } from "preact";

import { OverlayProps } from "../components/types";
import { fetchExperience } from "../services/api";
import { getGeolocation } from "../services/external/geolocation";
import { automaticallyApplyPreferences } from "./automated-consent";
import { getConsentContext } from "./consent-context";
import {
  ComponentType,
  FidesConfig,
  FidesCookie,
  FidesGlobal,
  FidesInitOptions,
  FidesOverrides,
  FidesWindowOverrides,
  NoticeValues,
  OverrideType,
  PrivacyExperience,
  UserGeolocation,
} from "./consent-types";
import {
  applyOverridesToConsent,
  constructFidesRegionString,
  experienceIsValid,
  getOverrideValidatorMapByType,
  getWindowObjFromPath,
  isPrivacyExperience,
  validateOptions,
} from "./consent-utils";
import {
  getCookieByName,
  getOrMakeFidesCookie,
  makeConsentDefaultsLegacy,
  updateCookieFromExperience,
} from "./cookie";
import {
  DEFAULT_LOCALE,
  DEFAULT_MODAL_LINK_LABEL,
  initializeI18n,
  localizeModalLinkText,
  setupI18n,
} from "./i18n";
import { UpdateExperienceProps } from "./init-utils";
import { searchForElement } from "./ui-utils";

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
      ),
    );
  }
  return fidesRegionString;
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
    const windowObj: FidesWindowOverrides | undefined =
      customPathArr && customPathArr.length >= 0
        ? getWindowObjFromPath(customPathArr)
        : (window.fides_overrides as FidesWindowOverrides);

    // Look for each of the override options in all three locations: query params, window object, cookie
    const overrideValidatorMap = getOverrideValidatorMapByType(type);
    overrideValidatorMap?.forEach(
      ({
        overrideName,
        overrideType,
        overrideKey,
        validationRegex,
        transform,
      }) => {
        const queryParamOverride: string | null = queryParams.get(overrideKey);
        const windowObjOverride: string | boolean | undefined = windowObj
          ? windowObj[overrideKey]
          : undefined;
        const cookieOverride: string | undefined = getCookieByName(overrideKey);

        // Load the override value, respecting the order of precedence (query params > window object > cookie)
        const value = queryParamOverride || windowObjOverride || cookieOverride;
        if (value && validationRegex.test(value.toString())) {
          // coerce to expected type
          if (transform) {
            overrides[overrideName as keyof T] = transform(value.toString());
          } else {
            overrides[overrideName as keyof T] =
              overrideType === "string" ? value : JSON.parse(value.toString());
          }
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
  const consentDefaults = makeConsentDefaultsLegacy(consent, context);

  // Load any existing user preferences from the browser cookie
  return getOrMakeFidesCookie(consentDefaults, options.fidesClearCookie);
};

/**
 * If saved preferences are detected, immediately initialize from local cache
 */
export const getInitialFidesFromConsent = ({
  cookie,
  savedConsent,
  experience,
  geolocation,
  options,
  updateExperienceFromCookieConsent,
}: {
  cookie: FidesCookie;
  savedConsent: NoticeValues;
} & FidesConfig & {
    updateExperienceFromCookieConsent: (props: {
      experience: PrivacyExperience;
      cookie: FidesCookie;
      debug: boolean;
    }) => PrivacyExperience;
  }): Partial<FidesGlobal> => {
  let updatedExperience = experience;
  if (isPrivacyExperience(experience)) {
    // at this point, a pre-fetched experience contains no user consent, so we populate with the Fides cookie. This method is passed in as a prop because it behaves differently for TCF than other experiences.
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
 * 2. Retrieves geolocation if necessary
 * 3. Retrieves experience if necessary
 * 4. Updates cookie as needed from the experience
 * 5. Initializes overlay components
 * 6. Applies automated consent (GPC, etc.) asynchronously if necessary
 */
export const initialize = async ({
  fides,
  options,
  geolocation,
  initOverlay,
  renderOverlay,
  updateExperience,
  overrides,
  propertyId,
}: {
  fides: FidesGlobal;
  initOverlay?: (
    props: OverlayProps & {
      renderOverlay?: (props: OverlayProps, parent: ContainerNode) => void;
    },
  ) => Promise<void>;
  renderOverlay?: (props: OverlayProps, parent: ContainerNode) => void;
  /**
   * Once we for sure have a valid experience, this is another chance to update values
   * before the overlay renders.
   */
  updateExperience: (
    props: UpdateExperienceProps,
  ) => Partial<PrivacyExperience>;
  overrides?: Partial<FidesOverrides>;
} & FidesConfig): Promise<Partial<FidesGlobal>> => {
  let shouldContinueInitOverlay: boolean = true;
  let fidesRegionString: string | null = null;
  let getModalLinkLabel: FidesGlobal["getModalLinkLabel"] = () =>
    DEFAULT_MODAL_LINK_LABEL;

  if (!fides.cookie) {
    throw new Error("Fides cookie should be initialized");
  }

  /**
   * If a property is using legacy consent, we should not initialize any
   * part of the overlay, not even Headless. Those properties will have
   * `isOverlayEnabled: false` in their config. `isOverlayEnabled` should
   * not be confused with Headless experiences, which are still considered
   * notice-based consent experiences.
   */
  const isNoticeBasedConsentEnabled = options.isOverlayEnabled;
  shouldContinueInitOverlay = isNoticeBasedConsentEnabled;

  if (shouldContinueInitOverlay) {
    if (!validateOptions(options)) {
      fidesDebugger(
        "Invalid config options. Skipping overlay initialization.",
        options,
      );
      shouldContinueInitOverlay = false;
    }

    fidesRegionString = await retrieveEffectiveRegionString(
      geolocation,
      options,
    );

    let fetchedClientSideExperience = false;

    if (!fidesRegionString) {
      fidesDebugger(
        `User location could not be obtained. Skipping overlay initialization.`,
      );
      shouldContinueInitOverlay = false;
    } else if (!isPrivacyExperience(fides.experience)) {
      fetchedClientSideExperience = true;
      // If no effective PrivacyExperience was pre-fetched, fetch one using the current region string
      // eslint-disable-next-line no-param-reassign
      fides.experience = await fetchExperience({
        userLocationString: fidesRegionString,
        fidesApiUrl: options.fidesApiUrl,
        apiOptions: options.apiOptions,
        requestMinimalTCF: false,
        propertyId,
      });
    }

    if (
      shouldContinueInitOverlay &&
      isPrivacyExperience(fides.experience) &&
      experienceIsValid(fides.experience)
    ) {
      /**
       * Now that we've determined the effective PrivacyExperience, update it
       * with some additional client-side state so that it is initialized with
       * the user's current consent preferences, etc. and ready to display!
       */
      if (fetchedClientSideExperience) {
        // If it's not client side fetched, we don't update anything since the cookie has already
        // been updated earlier.
        const updatedExperience = updateExperience({
          cookie: fides.cookie!,
          experience: fides.experience,
        });
        // eslint-disable-next-line no-param-reassign
        fides.experience = { ...fides.experience, ...updatedExperience };
        fidesDebugger(
          "Updated experience from saved preferences",
          updatedExperience,
        );
      }

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
      fidesDebugger(
        "Updated current cookie state from experience",
        updatedCookie,
      );
      // eslint-disable-next-line no-param-reassign
      fides.cookie = updatedCookie;

      // Initialize the i18n singleton before we render the overlay
      const i18n = setupI18n();
      initializeI18n(
        i18n,
        window?.navigator,
        fides.experience,
        options,
        overrides?.experienceTranslationOverrides,
      );

      // eslint-disable-next-line no-param-reassign
      fides.locale = i18n.locale || DEFAULT_LOCALE;

      // Provide the modal link label function to the client based on the current locale unless specified via props.
      getModalLinkLabel = (props) =>
        localizeModalLinkText(
          !!props?.disableLocalization,
          i18n,
          fides.experience,
        );

      /**
       * Now that we have the experience, translations, and modal link label,
       * we can render the modal link for the Headless experience.
       * With non-headless experiences, this will be handled by the overlay itself.
       */
      if (
        fides.experience.experience_config?.component === ComponentType.HEADLESS
      ) {
        const modalLinkId = options.modalLinkId || "fides-modal-link";
        const modalLinkIsDisabled =
          !fides.experience ||
          !!options.fidesEmbed ||
          options.modalLinkId === "";
        fidesDebugger("Fides overlay is disabled for this experience.");
        if (modalLinkIsDisabled) {
          fidesDebugger("Modal Link is disabled for this experience.");
        }
        fidesDebugger(`Searching for Modal link element #${modalLinkId}...`);
        searchForElement(modalLinkId).then((foundElement) => {
          fidesDebugger("Modal link element found, updating it to show");
          document.body.classList.add("fides-overlay-modal-link-shown");
          foundElement.classList.add("fides-modal-link-shown");
        });
        shouldContinueInitOverlay = false;
      }

      if (!!initOverlay && shouldContinueInitOverlay) {
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
          fidesDebugger(e);
        });
      }

      /**
       * Last up: apply automated preferences.
       *
       * NOTE: We want to finish initialization immediately while automated preferences
       * continue to run in the background. To ensure that any preference API calls
       * don't block the rest of the code from executing, we use setTimeout with
       * no delay which simply moves it to the end of the JavaScript event queue.
       */
      setTimeout(
        automaticallyApplyPreferences.bind(null, {
          savedConsent: fides.saved_consent,
          effectiveExperience: fides.experience as PrivacyExperience,
          cookie: fides.cookie,
          fidesRegionString,
          fidesOptions: options,
          i18n,
        }),
      );
    } else {
      fidesDebugger("Skipping overlay initialization.", fides.experience);
    }
  }

  // eslint-disable-next-line @typescript-eslint/naming-convention
  const { fides_meta, identity, fides_string, tcf_consent } = fides.cookie;

  // used to set Fides.consent
  const consent = applyOverridesToConsent(
    fides.cookie.consent,
    fides.experience?.non_applicable_privacy_notices,
    fides.experience?.privacy_notices,
    options.fidesConsentFlagType ?? undefined,
    options.fidesConsentNonApplicableFlagMode ?? undefined,
  );

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
