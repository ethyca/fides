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
  PrivacyPreferencesRequest,
  SaveConsentPreference,
  UpdateConsentValidation,
  UserConsentPreference,
} from "./consent-types";
import {
  applyOverridesToConsent,
  constructFidesRegionString,
} from "./consent-utils";
import {
  removeCookiesFromBrowser,
  saveFidesCookie,
  updateCookieFromNoticePreferences,
} from "./cookie";
import { dispatchFidesEvent, FidesEventDetailsTrigger } from "./events";
import { decodeFidesString } from "./fides-string";
import { transformConsentToFidesUserPreference } from "./shared-consent-utils";
import { TcfSavePreferences } from "./tcf/types";
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
  propertyId?: string,
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
    property_id: propertyId,
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

/**
 * Updates the user's consent preferences, going through the following steps:
 * 1. Update the cookie object based on new preferences
 * 2. Dispatch a "FidesUpdating" event with the new preferences
 * 3. Update the window.Fides object
 * 4. Save preferences to the `fides_consent` cookie in the browser
 * 5. Save preferences to Fides API or a custom function (`savePreferencesFn`)
 * 6. Remove any cookies from notices that were opted-out from the browser
 * 7. Dispatch a "FidesUpdated" event
 */
export interface UpdateConsentPreferences {
  consentPreferencesToSave?: Array<SaveConsentPreference>;
  privacyExperienceConfigHistoryId?: string;
  experience: PrivacyExperience | PrivacyExperienceMinimal;
  consentMethod: ConsentMethod;
  options: FidesInitOptions;
  userLocationString?: string;
  cookie: FidesCookie;
  eventTrigger?: FidesEventDetailsTrigger;
  servedNoticeHistoryId?: string;
  tcf?: TcfSavePreferences;
  updateCookie?: (oldCookie: FidesCookie) => Promise<FidesCookie>;
  propertyId?: string;
}
export const updateConsentPreferences = async ({
  consentPreferencesToSave,
  privacyExperienceConfigHistoryId,
  experience,
  consentMethod,
  options,
  userLocationString,
  cookie,
  eventTrigger,
  servedNoticeHistoryId,
  tcf,
  updateCookie,
  propertyId,
}: UpdateConsentPreferences) => {
  if (!updateCookie && consentPreferencesToSave) {
    // eslint-disable-next-line no-param-reassign
    updateCookie = (oldCookie) =>
      updateCookieFromNoticePreferences(oldCookie, consentPreferencesToSave);
  }
  if (!updateCookie && !consentPreferencesToSave) {
    throw new Error("updateCookie is required");
  }
  const trigger = {
    ...eventTrigger,
    origin:
      eventTrigger?.origin ||
      (consentMethod === ConsentMethod.SCRIPT ||
      consentMethod === ConsentMethod.GPC ||
      consentMethod === ConsentMethod.OT_MIGRATION
        ? "external"
        : "fides"),
  };
  // 1. Update the cookie object based on new preferences & extra details
  const updatedCookie = await updateCookie!(cookie);
  Object.assign(cookie, updatedCookie);
  Object.assign(cookie.fides_meta, { consentMethod }); // save extra details to meta (i.e. consentMethod)

  // 2. Dispatch a "FidesUpdating" event with the new preferences
  dispatchFidesEvent("FidesUpdating", cookie, {
    trigger,
  });

  // 3. Update the window.Fides object
  fidesDebugger("Updating window.Fides");
  const normalizedConsent = applyOverridesToConsent(
    cookie.consent,
    window.Fides?.experience?.non_applicable_privacy_notices,
    window.Fides?.experience?.privacy_notices,
  );
  window.Fides.consent = normalizedConsent;
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
        propertyId,
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
    trigger,
  });
};

const validateConsent = (fides: FidesGlobal, consent: NoticeConsent) => {
  return Object.entries(consent).reduce<Error | null>((error, [key, value]) => {
    // If we already found an error, don't continue validating
    if (error) {
      return error;
    }

    const nonApplicableNotice =
      fides.experience!.non_applicable_privacy_notices?.find((n) => n === key);

    if (nonApplicableNotice) {
      return new Error(
        `Provided notice key '${key}' is not applicable to the current experience.`,
      );
    }

    const notice = fides.experience!.privacy_notices?.find(
      (n) => n.notice_key === key,
    );

    if (!nonApplicableNotice && !notice) {
      return new Error(`'${key}' is not a valid notice key`);
    }

    const consentMechanism = notice?.consent_mechanism;
    const isNoticeOnly = consentMechanism === ConsentMechanism.NOTICE_ONLY;

    if (
      isNoticeOnly &&
      value !== true &&
      value !== UserConsentPreference.ACKNOWLEDGE
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
export const updateConsent = async (
  fides: FidesGlobal,
  options: {
    consent?: NoticeConsent;
    fidesString?: string;
    validation?: UpdateConsentValidation;
  },
  consentMethod: ConsentMethod = ConsentMethod.SCRIPT,
  eventTrigger: FidesEventDetailsTrigger = {
    origin: "external",
  },
): Promise<void> => {
  // If neither consent nor fidesString is provided, raise an error
  if (!options?.consent && !options?.fidesString) {
    throw new Error("Either consent or fidesString must be provided");
  }
  if (!fides.experience) {
    throw new Error("Experience must be initialized before updating consent");
  }
  if (!fides.cookie) {
    throw new Error("Cookie is not initialized");
  }
  const {
    consent,
    fidesString,
    validation = UpdateConsentValidation.THROW,
  } = options;

  if (!Object.values(UpdateConsentValidation).includes(validation)) {
    throw new Error(
      `Validation must be one of: ${Object.values(UpdateConsentValidation).join(
        ", ",
      )} (default is ${UpdateConsentValidation.THROW})`,
    );
  }

  const handleValidationError = (errorMessage: string) => {
    if (validation === UpdateConsentValidation.THROW) {
      throw new Error(errorMessage);
    }
    if (validation === UpdateConsentValidation.WARN) {
      // eslint-disable-next-line no-console
      console.warn(errorMessage);
    }
  };

  let finalConsent = fides.consent || {};

  // validate consent object
  if (consent) {
    // Validate consent values and collect any validation errors
    const validationError = validateConsent(fides, consent);

    if (validationError) {
      handleValidationError(validationError.message);
    }
  }

  // If fidesString is provided, it takes priority
  if (fidesString) {
    try {
      const decodedString = decodeFidesString(fidesString);
      if (decodedString.nc) {
        finalConsent = {
          ...fides.consent,
          ...fides.decodeNoticeConsentString(decodedString.nc),
        };
        const validationError = validateConsent(fides, finalConsent);

        if (validationError) {
          handleValidationError(validationError.message);
        }
      }
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : String(error);
      handleValidationError(`Invalid fidesString provided: ${errorMessage}`);
    }
  } else {
    finalConsent = { ...fides.consent, ...consent };
  }

  // Prepare consentPreferencesToSave by mapping from finalConsent
  const consentPreferencesToSave: SaveConsentPreference[] = [];

  Object.entries(finalConsent).forEach(([key, value]) => {
    const notice = fides.experience?.privacy_notices?.find(
      (n) => n.notice_key === key,
    );
    // non-applicable privacy notices are ignored
    if (notice) {
      const historyId = notice.translations?.[0]?.privacy_notice_history_id;
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
        consentPreferencesToSave.push(
          new SaveConsentPreference(notice, consentPreference, historyId),
        );
      }
    }
  });

  // Get privacy_experience_config_history_id from experience config translations
  let configHistoryId: string | undefined;
  if (fides.experience.experience_config?.translations?.length) {
    configHistoryId =
      fides.experience.experience_config.translations[0]
        .privacy_experience_config_history_id;
  }

  const fidesRegionString =
    constructFidesRegionString(fides.geolocation) || undefined;

  // Call updateConsentPreferences with necessary parameters
  return updateConsentPreferences({
    consentPreferencesToSave,
    privacyExperienceConfigHistoryId: configHistoryId,
    experience: fides.experience as
      | PrivacyExperience
      | PrivacyExperienceMinimal,
    consentMethod,
    options: fides.options,
    userLocationString: fidesRegionString,
    cookie: fides.cookie,
    propertyId: fides.config?.propertyId,
    eventTrigger,
  });
};
