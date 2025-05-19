import { patchUserPreference } from "../services/api";
import {
  ConsentMethod,
  ConsentOptionCreate,
  FidesCookie,
  FidesGlobal,
  FidesInitOptions,
  NoticeValues,
  PrivacyExperience,
  PrivacyExperienceMinimal,
  PrivacyPreferencesRequest,
  SaveConsentPreference,
  UserConsentPreference,
} from "./consent-types";
import {
  applyOverridesToConsent,
  constructFidesRegionString,
} from "./consent-utils";
import { removeCookiesFromBrowser, saveFidesCookie } from "./cookie";
import { dispatchFidesEvent } from "./events";
import { decodeFidesString } from "./fides-string";
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
  servedNoticeHistoryId?: string;
  tcf?: TcfSavePreferences;
  updateCookie: (oldCookie: FidesCookie) => Promise<FidesCookie>;
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
  servedNoticeHistoryId,
  tcf,
  updateCookie,
  propertyId,
}: UpdateConsentPreferences) => {
  // 1. Update the cookie object based on new preferences & extra details
  const updatedCookie = await updateCookie(cookie);
  Object.assign(cookie, updatedCookie);
  Object.assign(cookie.fides_meta, { consentMethod }); // save extra details to meta (i.e. consentMethod)

  // 2. Dispatch a "FidesUpdating" event with the new preferences
  dispatchFidesEvent("FidesUpdating", cookie, options.debug);

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
  dispatchFidesEvent("FidesUpdated", cookie, options.debug);
};

/**
 * Updates user consent preferences with either a consent object or fidesString.
 * If both are provided, fidesString takes priority.
 * Can be used as a convenience method to update consent preferences using the FidesGlobal object.
 */
export const updateConsent = async (
  fides: FidesGlobal,
  options: { consent?: NoticeValues; fidesString?: string },
): Promise<void> => {
  // If neither consent nor fidesString is provided, raise an error
  if (!options?.consent && !options?.fidesString) {
    return Promise.reject(
      new Error("Either consent or fidesString must be provided"),
    );
  }

  const { consent, fidesString } = options;

  let finalConsent = consent || {};

  // If fidesString is provided, it takes priority
  if (fidesString) {
    try {
      const decodedString = decodeFidesString(fidesString);
      if (decodedString.nc) {
        finalConsent = fides.decodeNoticeConsentString(decodedString.nc);
      }
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : String(error);
      return Promise.reject(
        new Error(`Invalid fidesString provided: ${errorMessage}`),
      );
    }
  }

  // Clone current cookie for updating
  if (!fides.cookie) {
    return Promise.reject(new Error("Cookie is not initialized"));
  }

  const updatedCookie: FidesCookie = {
    consent: { ...(fides.cookie.consent || {}) },
    identity: { ...(fides.cookie.identity || {}) },
    fides_meta: { ...(fides.cookie.fides_meta || {}) },
    tcf_consent: { ...(fides.cookie.tcf_consent || {}) },
    fides_string: fides.cookie.fides_string || "",
    tcf_version_hash: fides.cookie.tcf_version_hash || "",
  };

  // Update cookie with new consent values
  Object.entries(finalConsent).forEach(([key, value]) => {
    updatedCookie.consent[key] = value;
  });

  // If fidesString is provided, update it on the cookie
  if (fidesString) {
    updatedCookie.fides_string = fidesString;
  } else if (consent) {
    // Generate new fidesString based on updated consent
    const newNcString = fides.encodeNoticeConsentString(finalConsent);
    // Preserve other parts of fidesString if they exist
    if (fides.cookie.fides_string) {
      const decoded = decodeFidesString(fides.cookie.fides_string);
      decoded.nc = newNcString;
      updatedCookie.fides_string = `${decoded.tc || ""}.${newNcString}.${decoded.gpp || ""}`;
    } else {
      updatedCookie.fides_string = `.${newNcString}.`;
    }
  }

  if (!fides.experience) {
    return Promise.reject(
      new Error("Experience must be initialized before updating consent"),
    );
  }

  // Prepare consentPreferencesToSave by mapping from finalConsent
  const consentPreferencesToSave: SaveConsentPreference[] = [];

  // Validate that all notice keys in finalConsent exist in the experience
  const validNoticeKeys = new Set(
    fides.experience.privacy_notices?.map((n) => n.notice_key) || [],
  );

  Object.entries(finalConsent).forEach(([key, value]) => {
    if (!validNoticeKeys.has(key)) {
      fidesDebugger(
        `Warning: Notice key "${key}" does not exist in the current experience`,
      );
      // Continue processing other keys
    }

    const notice = fides.experience?.privacy_notices?.find(
      (n) => n.notice_key === key,
    );
    if (notice) {
      const historyId = notice.translations?.[0]?.privacy_notice_history_id;
      if (historyId) {
        consentPreferencesToSave.push(
          new SaveConsentPreference(
            notice,
            value
              ? UserConsentPreference.OPT_IN
              : UserConsentPreference.OPT_OUT,
            historyId,
          ),
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
    consentMethod: ConsentMethod.SAVE,
    options: fides.options,
    userLocationString: fidesRegionString,
    cookie: fides.cookie,
    servedNoticeHistoryId: undefined, // Not passing a served notice ID
    updateCookie: async () => updatedCookie,
    propertyId: fides.config?.propertyId,
  });
};
