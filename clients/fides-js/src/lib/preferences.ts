import {
  ConsentMethod,
  FidesCookie,
  FidesOptions,
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
  options: FidesOptions,
  cookie: FidesCookie,
  experience: PrivacyExperience,
  consentMethod: ConsentMethod,
  consentPreferencesToSave?: Array<SaveConsentPreference>,
  tcf?: TcfSavePreferences,
  userLocationString?: string,
  servedNoticeHistoryId?: string
) {
  debugLog(options.debug, "Saving preferences to Fides API");
  // Derive the Fides user preferences array from consent preferences
  // TODO (PROD-1597): pass in specific language shown in UI
  const fidesUserPreferences = consentPreferencesToSave?.map((preference) => ({
    privacy_notice_history_id:
      preference.notice.translations[0].privacy_notice_history_id,
    preference: preference.consentPreference,
  }));
  const privacyPreferenceCreate: PrivacyPreferencesRequest = {
    browser_identity: cookie.identity,
    preferences: fidesUserPreferences,
    // TODO (PROD-1597): pass in specific language shown in UI
    privacy_experience_id:
      experience.experience_config?.translations[0]
        .privacy_experience_config_history_id,
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
 * 3. Save preferences to Fides API or a custom function (`savePreferencesFn`)
 * 4. Save preferences to the `fides_consent` cookie in the browser
 * 5. Remove any cookies from notices that were opted-out from the browser
 * 6. Dispatch a "FidesUpdated" event
 */
export const updateConsentPreferences = async ({
  consentPreferencesToSave,
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
  experience: PrivacyExperience;
  consentMethod: ConsentMethod;
  options: FidesOptions;
  userLocationString?: string;
  cookie: FidesCookie;
  debug?: boolean;
  servedNoticeHistoryId?: string;
  tcf?: TcfSavePreferences;
  updateCookie: (oldCookie: FidesCookie) => Promise<FidesCookie>;
}) => {
  if (options.fidesPreviewMode) {
    // Shouldn't be hit in preview mode, but just in case, we ensure we never write a Fides Cookie
    return;
  }
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

  // 3. Save preferences to API (if not disabled)
  if (!options.fidesDisableSaveApi) {
    try {
      await savePreferencesApi(
        options,
        cookie,
        experience,
        consentMethod,
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

  // 4. Save preferences to the cookie in the browser
  debugLog(options.debug, "Saving preferences to cookie");
  saveFidesCookie(cookie, options.base64Cookie);

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
