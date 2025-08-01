import { patchUserPreference } from "../services/api";
import {
  ConsentMechanism,
  ConsentMethod,
  ConsentOptionCreate,
  FidesCookie,
  FidesGlobal,
  FidesInitOptions,
  NoticeConsent,
  NoticeValues,
  PrivacyExperience,
  PrivacyExperienceMinimal,
  PrivacyNotice,
  PrivacyNoticeWithPreference,
  PrivacyPreferencesRequest,
  SaveConsentPreference,
  UpdateConsentValidation,
  UserConsentPreference,
} from "./consent-types";
import {
  applyOverridesToConsent,
  constructFidesRegionString,
  createConsentProxy,
  decodeNoticeConsentString,
} from "./consent-utils";
import {
  removeCookiesFromBrowser,
  saveFidesCookie,
  updateCookieFromNoticePreferences,
} from "./cookie";
import {
  dispatchFidesEvent,
  FidesEventDetailsTrigger,
  FidesEventExtraDetails,
  FidesEventOrigin,
} from "./events";
import { fidesLifecycleManager } from "./fides-lifecycle-manager";
import { decodeFidesString } from "./fides-string";
import {
  DEFAULT_LOCALE,
  extractDefaultLocaleFromExperience,
  selectBestExperienceConfigTranslation,
  selectBestNoticeTranslation,
} from "./i18n";
import { transformConsentToFidesUserPreference } from "./shared-consent-utils";
import { TcfSavePreferences } from "./tcf/types";

const EXTERNAL_CONSENT_METHODS = [
  ConsentMethod.SCRIPT,
  ConsentMethod.GPC,
  ConsentMethod.OT_MIGRATION,
];

/**
 * Helper function to transform save prefs and call API
 */
async function savePreferencesApi(
  options: FidesInitOptions,
  cookie: FidesCookie,
  experience: PrivacyExperience | PrivacyExperienceMinimal,
  consentMethod: ConsentMethod,
  privacyExperienceConfigHistoryId?: string,
  consentPreferencesToSave?: Array<
    Pick<SaveConsentPreference, "noticeHistoryId" | "consentPreference">
  >,
  tcf?: TcfSavePreferences,
  userLocationString?: string,
  servedNoticeHistoryId?: string,
) {
  fidesDebugger("Saving preferences to Fides API");
  // Derive the Fides user preferences array from consent preferences
  const fidesUserPreferences: ConsentOptionCreate[] = (
    consentPreferencesToSave || []
  ).map((preference) => ({
    preference: preference.consentPreference,
    privacy_notice_history_id: preference.noticeHistoryId || "",
  }));

  const privacyPreferenceCreate: PrivacyPreferencesRequest = {
    browser_identity: cookie.identity,
    preferences: fidesUserPreferences,
    privacy_experience_config_history_id: privacyExperienceConfigHistoryId,
    user_geography: userLocationString,
    method: consentMethod,
    served_notice_history_id: servedNoticeHistoryId,
    property_id: experience.property_id,
    ...(tcf ?? []),
  };
  await patchUserPreference(
    consentMethod,
    privacyPreferenceCreate,
    options,
    cookie,
    experience,
  );
}

interface UpdateConsentPreferencesProps {
  consentPreferencesToSave?: Array<SaveConsentPreference>;
  privacyExperienceConfigHistoryId?: string;
  experience: PrivacyExperience | PrivacyExperienceMinimal;
  consentMethod: ConsentMethod;
  options: FidesInitOptions;
  userLocationString?: string;
  cookie: FidesCookie;
  eventExtraDetails?: FidesEventExtraDetails;
  servedNoticeHistoryId?: string;
  tcf?: TcfSavePreferences;
  updateCookie?: (oldCookie: FidesCookie) => Promise<FidesCookie>;
}
/**
 * Updates the user's consent preferences, going through the following steps:
 * 1. Update the cookie object based on new preferences
 * 2. Dispatch a "FidesUpdating" event with the new preferences
 * 3. Update the window.Fides object
 * 4. Save preferences to the `fides_consent` cookie in the browser
 * 5. Save preferences to Fides API or a custom function (`savePreferencesFn`)
 * 6. Remove any cookies from notices that were opted-out from the browser
 * 7. Dispatch a "FidesUpdated" event
 * NOTE: only exported for use by unit tests, use updateConsent instead.
 */
export const updateConsentPreferences = async ({
  consentPreferencesToSave,
  privacyExperienceConfigHistoryId,
  experience,
  consentMethod,
  options,
  userLocationString,
  cookie,
  eventExtraDetails,
  servedNoticeHistoryId,
  tcf,
  updateCookie,
}: UpdateConsentPreferencesProps) => {
  if (!updateCookie && consentPreferencesToSave) {
    // eslint-disable-next-line no-param-reassign
    updateCookie = (oldCookie) =>
      updateCookieFromNoticePreferences(oldCookie, consentPreferencesToSave);
  }
  if (!updateCookie && !consentPreferencesToSave) {
    throw new Error("updateCookie is required");
  }
  const trigger: FidesEventDetailsTrigger = {
    ...(eventExtraDetails?.trigger as FidesEventDetailsTrigger),
    origin:
      (eventExtraDetails?.trigger as FidesEventDetailsTrigger)?.origin ||
      (EXTERNAL_CONSENT_METHODS.includes(consentMethod)
        ? FidesEventOrigin.EXTERNAL
        : FidesEventOrigin.FIDES),
  };
  // 1. Update the cookie object based on new preferences & extra details
  const updatedCookie = await updateCookie!(cookie);
  Object.assign(cookie, updatedCookie);
  Object.assign(cookie.fides_meta, { consentMethod }); // save extra details to meta (i.e. consentMethod)

  // 2. Dispatch a "FidesUpdating" event with the new preferences
  dispatchFidesEvent("FidesUpdating", cookie, {
    ...eventExtraDetails,
    trigger,
  });

  // 3. Update the window.Fides object
  fidesDebugger("Updating window.Fides");
  const normalizedConsent = applyOverridesToConsent(
    cookie.consent,
    window.Fides?.experience?.non_applicable_privacy_notices,
    window.Fides?.experience?.privacy_notices,
  );
  const hasPrivacyNotices =
    !!window.Fides?.experience?.non_applicable_privacy_notices ||
    !!window.Fides?.experience?.privacy_notices;
  window.Fides.consent = createConsentProxy(
    normalizedConsent,
    options,
    hasPrivacyNotices,
  );
  window.Fides.fides_string = cookie.fides_string;
  window.Fides.tcf_consent = cookie.tcf_consent;

  // 4. Save preferences to the cookie in the browser
  fidesDebugger("Saving preferences to cookie");
  saveFidesCookie(
    { ...cookie, consent: normalizedConsent },
    options.base64Cookie,
  );
  window.Fides.saved_consent = cookie.consent as NoticeValues;

  // 5. Save preferences to API (if not disabled)
  if (!options.fidesDisableSaveApi) {
    try {
      await savePreferencesApi(
        options,
        cookie,
        experience,
        consentMethod,
        privacyExperienceConfigHistoryId,
        consentPreferencesToSave,
        tcf,
        userLocationString,
        servedNoticeHistoryId,
      );
    } catch (e) {
      fidesDebugger(
        "Error saving updated preferences to API, continuing. Error: ",
        e,
      );
    }
  }

  // 6. Remove cookies associated with notices that were opted-out from the browser
  if (consentPreferencesToSave) {
    consentPreferencesToSave
      .filter(
        (preference) =>
          preference.consentPreference === UserConsentPreference.OPT_OUT,
      )
      .forEach((preference) => {
        if (preference.notice?.cookies) {
          removeCookiesFromBrowser(
            preference.notice.cookies,
            experience.experience_config?.auto_subdomain_cookie_deletion,
          );
        }
      });
  }

  // 7. Dispatch a "FidesUpdated" event
  dispatchFidesEvent("FidesUpdated", cookie, {
    ...eventExtraDetails,
    trigger,
  });
};

const validateConsent = (
  privacyNotices: PrivacyNoticeWithPreference[],
  nonApplicablePrivacyNotices: PrivacyNotice["notice_key"][],
  consent: NoticeConsent,
  consentMethod: ConsentMethod,
) => {
  return Object.entries(consent).reduce<Error | null>((error, [key, value]) => {
    // If we already found an error, don't continue validating
    if (error) {
      return error;
    }

    const nonApplicableNotice = nonApplicablePrivacyNotices.find(
      (n) => n === key,
    );

    if (
      nonApplicableNotice &&
      !value &&
      consentMethod !== ConsentMethod.OT_MIGRATION
    ) {
      return new Error(
        `Provided notice key '${key}' is not applicable to the current experience.`,
      );
    }

    const notice = privacyNotices.find((n) => n.notice_key === key);

    if (!nonApplicableNotice && !notice) {
      return new Error(`'${key}' is not a valid notice key`);
    }

    const consentMechanism = notice?.consent_mechanism;
    const isNoticeOnly = consentMechanism === ConsentMechanism.NOTICE_ONLY;

    if (
      isNoticeOnly &&
      value !== true &&
      value !== UserConsentPreference.ACKNOWLEDGE &&
      consentMethod !== ConsentMethod.OT_MIGRATION
    ) {
      return new Error(
        `Invalid consent value for notice-only notice key: '${key}'. Must be \`true\` or "acknowledge"`,
      );
    }

    if (
      !isNoticeOnly &&
      typeof value !== "boolean" &&
      value !== UserConsentPreference.OPT_IN &&
      value !== UserConsentPreference.OPT_OUT
    ) {
      return new Error(
        `Invalid consent value for notice key: '${key}'. Must be a boolean or "opt_in" or "opt_out"`,
      );
    }

    return null;
  }, null);
};

/**
 * Updates user consent preferences with either a consent object or fidesString.
 * If both are provided, fidesString takes priority.
 * Can be used as a convenience method to update consent preferences using the FidesGlobal object.
 */
export interface UpdateConsentOptions {
  noticeConsent?: NoticeConsent;
  fidesString?: string;
  validation?: UpdateConsentValidation;
  consentMethod?: ConsentMethod;
  eventExtraDetails?: FidesEventExtraDetails;
  tcf?: TcfSavePreferences;
  updateCookie?: (oldCookie: FidesCookie) => Promise<FidesCookie>;
}
export const updateConsent = async (
  context: Pick<FidesGlobal, "experience" | "cookie" | "config" | "locale">,
  consentOptions: UpdateConsentOptions,
): Promise<void> => {
  const { experience, cookie, config, locale } = context;
  if (!experience) {
    throw new Error("Experience must be initialized before updating consent");
  }
  if (!config) {
    throw new Error("Config is not initialized");
  }
  if (!cookie) {
    throw new Error("Cookie is not initialized");
  }
  // If neither consent nor fidesString is provided, raise an error
  // Note: this error primarily benefits customers using the window.Fides.updateConsent API,
  // which doesn't support TCF. That's why we don't call out TCF in the error message.
  if (
    !consentOptions?.noticeConsent &&
    !consentOptions?.fidesString &&
    !consentOptions?.tcf
  ) {
    throw new Error("Either consent object or fidesString must be provided");
  }
  if (
    consentOptions?.validation &&
    !Object.values(UpdateConsentValidation).includes(consentOptions.validation)
  ) {
    throw new Error(
      `Validation must be one of: ${Object.values(UpdateConsentValidation).join(
        ", ",
      )} (default is ${UpdateConsentValidation.THROW})`,
    );
  }

  const {
    noticeConsent,
    fidesString,
    validation = UpdateConsentValidation.THROW,
    consentMethod = ConsentMethod.SCRIPT,
    eventExtraDetails = {
      trigger: {
        origin: FidesEventOrigin.EXTERNAL,
      },
    },
    tcf,
    updateCookie,
  } = consentOptions;

  const {
    experience_config: experienceConfig,
    privacy_notices: privacyNotices,
    non_applicable_privacy_notices: nonApplicablePrivacyNotices,
  } = experience;

  const defaultLocale =
    extractDefaultLocaleFromExperience(experience as PrivacyExperience) ||
    DEFAULT_LOCALE;

  /**
   * This mostly exists to support the Fides.updateConsent API which
   * allows end users to pass in a preference for validation behavior.
   */
  const handleValidationError = (errorMessage: string) => {
    if (validation === UpdateConsentValidation.THROW) {
      throw new Error(errorMessage);
    }
    if (validation === UpdateConsentValidation.WARN) {
      // eslint-disable-next-line no-console
      console.warn(errorMessage);
    }
  };

  let finalConsent = cookie.consent || {};

  // If fidesString is provided, it takes priority
  if (fidesString) {
    try {
      const decodedString = decodeFidesString(fidesString);
      if (decodedString.nc) {
        const decodedConsent = decodeNoticeConsentString(decodedString.nc);
        finalConsent = {
          ...cookie.consent,
          ...decodedConsent,
        };
        const validationError = validateConsent(
          privacyNotices || [],
          nonApplicablePrivacyNotices || [],
          finalConsent,
          consentMethod,
        );

        if (validationError) {
          handleValidationError(validationError.message);
        }
      }
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : String(error);
      handleValidationError(`Invalid fidesString provided: ${errorMessage}`);
    }
  } else if (noticeConsent) {
    // Validate consent values and collect any validation errors
    const validationError = validateConsent(
      privacyNotices || [],
      nonApplicablePrivacyNotices || [],
      noticeConsent,
      consentMethod,
    );

    if (validationError) {
      handleValidationError(validationError.message);
    }
    finalConsent = { ...cookie.consent, ...noticeConsent };
  }

  // Prepare consentPreferencesToSave by mapping from finalConsent
  const consentPreferencesToSave: SaveConsentPreference[] = [];

  Object.entries(finalConsent).forEach(([key, value]) => {
    const notice = privacyNotices?.find((n) => n.notice_key === key);
    // non-applicable privacy notices are ignored
    if (notice) {
      const bestNoticeTranslation = selectBestNoticeTranslation(
        locale,
        defaultLocale,
        notice,
      );
      const historyId = bestNoticeTranslation?.privacy_notice_history_id;
      let consentPreference: UserConsentPreference;
      if (typeof value === "boolean") {
        consentPreference = transformConsentToFidesUserPreference(
          value,
          notice.consent_mechanism,
        );
      } else {
        consentPreference = value;
      }

      if (historyId) {
        const savedConsentPreference = new SaveConsentPreference(
          notice,
          consentPreference,
          historyId,
        );
        consentPreferencesToSave.push(savedConsentPreference);
      }
    }
  });

  // Get privacy_experience_config_history_id from experience config translations
  let configHistoryId: string | undefined;
  if (experienceConfig?.translations?.length) {
    const bestExperienceConfigTranslation =
      selectBestExperienceConfigTranslation(
        locale,
        defaultLocale,
        experienceConfig,
      );
    configHistoryId =
      bestExperienceConfigTranslation?.privacy_experience_config_history_id;
  }

  const fidesRegionString = constructFidesRegionString(config.geolocation);

  // Get the lifecycle-level served notice history ID for consistency
  const servedNoticeHistoryId =
    fidesLifecycleManager.getServedNoticeHistoryId();

  // Call updateConsentPreferences with necessary parameters
  return updateConsentPreferences({
    consentPreferencesToSave,
    privacyExperienceConfigHistoryId: configHistoryId,
    experience: experience as PrivacyExperience | PrivacyExperienceMinimal,
    consentMethod,
    options: config.options,
    userLocationString: fidesRegionString,
    cookie,
    eventExtraDetails,
    servedNoticeHistoryId,
    tcf,
    updateCookie,
  });
};
