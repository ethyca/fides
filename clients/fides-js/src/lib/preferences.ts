import {
  ConsentMethod,
  ConsentOptionCreate,
  FidesCookie,
  FidesInitOptions,
  PrivacyExperience,
  PrivacyPreferencesRequest,
  SaveConsentPreference,
  UserConsentPreference,
} from "./consent-types";
import { debugLog } from "./consent-utils";
import { removeCookiesFromBrowser, saveFidesCookie } from "./cookie";
import { dispatchFidesEvent, FidesEventExtraDetails } from "./events";
import { patchUserPreference } from "../services/api";
import { TcfSavePreferences } from "./tcf/types";

/**
 * Helper function to transform save prefs and call API
 */
async function savePreferencesApi(
  options: FidesInitOptions,
  cookie: FidesCookie,
  experience: PrivacyExperience,
  consentMethod: ConsentMethod,
  privacyExperienceConfigHistoryId?: string,
  consentPreferencesToSave?: Array<SaveConsentPreference>,
  tcf?: TcfSavePreferences,
  userLocationString?: string,
  servedNoticeHistoryId?: string
) {
  debugLog(options.debug, "Saving preferences to Fides API");
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
    ...(tcf ?? []),
  };
  await patchUserPreference(
    consentMethod,
    privacyPreferenceCreate,
    options,
    cookie,
    experience
  );
}

/**
 * Updates the user's consent preferences, going through the following steps:
 * 1. Update the cookie object based on new preferences
 * 2. Update the window.Fides object
 * 3. Save preferences to the `fides_consent` cookie in the browser
 * 4. Save preferences to Fides API or a custom function (`savePreferencesFn`)
 * 5. Remove any cookies from notices that were opted-out from the browser
 * 6. Dispatch a "FidesUpdated" event
 */
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
}: {
  consentPreferencesToSave?: Array<SaveConsentPreference>;
  privacyExperienceConfigHistoryId?: string;
  experience: PrivacyExperience;
  consentMethod: ConsentMethod;
  options: FidesInitOptions;
  userLocationString?: string;
  cookie: FidesCookie;
  debug?: boolean;
  servedNoticeHistoryId?: string;
  tcf?: TcfSavePreferences;
  updateCookie: (oldCookie: FidesCookie) => Promise<FidesCookie>;
}) => {
  // Collect any "extra" details that should be recorded on the cookie & event
  const extraDetails: FidesEventExtraDetails = { consentMethod };

  // 1. Update the cookie object based on new preferences & extra details
  const updatedCookie = await updateCookie(cookie);
  Object.assign(cookie, updatedCookie);
  Object.assign(cookie.fides_meta, extraDetails); // save extra details to meta (i.e. consentMethod)

  // 2. Update the window.Fides object
  debugLog(options.debug, "Updating window.Fides");
  window.Fides.consent = cookie.consent;
  window.Fides.fides_string = cookie.fides_string;
  window.Fides.tcf_consent = cookie.tcf_consent;

  // 3. Save preferences to the cookie in the browser
  debugLog(options.debug, "Saving preferences to cookie");
  saveFidesCookie(cookie, options.base64Cookie);
  window.Fides.saved_consent = cookie.consent;

  // 4. Save preferences to API (if not disabled)
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
        servedNoticeHistoryId
      );
    } catch (e) {
      debugLog(
        options.debug,
        "Error saving updated preferences to API, continuing. Error: ",
        e
      );
    }
  }

  // 5. Remove cookies associated with notices that were opted-out from the browser
  if (consentPreferencesToSave) {
    consentPreferencesToSave
      .filter(
        (preference) =>
          preference.consentPreference === UserConsentPreference.OPT_OUT
      )
      .forEach((preference) => {
        removeCookiesFromBrowser(preference.notice.cookies);
      });
  }

  // 6. Dispatch a "FidesUpdated" event
  dispatchFidesEvent("FidesUpdated", cookie, options.debug, extraDetails);
};
