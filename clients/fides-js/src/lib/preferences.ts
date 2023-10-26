import {
  ConsentMethod,
  FidesOptions,
  LastServedConsentSchema,
  PrivacyExperience,
  PrivacyPreferencesRequest,
  SaveConsentPreference,
  UserConsentPreference,
} from "./consent-types";
import { debugLog } from "./consent-utils";
import {
  FidesCookie,
  removeCookiesFromBrowser,
  saveFidesCookie,
} from "./cookie";
import { dispatchFidesEvent } from "./events";
import { patchUserPreferenceToFidesServer } from "../services/fides/api";
import { TcfSavePreferences } from "./tcf/types";

/**
 * Helper function to save preferences to an API, either custom or internal
 */
async function savePreferencesApi(
  options: FidesOptions,
  cookie: FidesCookie,
  experience: PrivacyExperience,
  consentMethod: ConsentMethod,
  consentPreferencesToSave?: Array<SaveConsentPreference>,
  tcf?: TcfSavePreferences,
  userLocationString?: string
) {
  if (options.apiOptions?.savePreferencesFn) {
    debugLog(options.debug, "Calling custom save preferences fn");
    await options.apiOptions.savePreferencesFn(
      cookie.consent,
      cookie.fides_string,
      experience
    );
  } else {
    debugLog(options.debug, "Saving preferences to Fides API");
    // Derive the Fides user preferences array from consent preferences
    const fidesUserPreferences = consentPreferencesToSave?.map(
      (preference) => ({
        privacy_notice_history_id: preference.notice.privacy_notice_history_id,
        preference: preference.consentPreference,
        served_notice_history_id: preference.servedNoticeHistoryId,
      })
    );
    const privacyPreferenceCreate: PrivacyPreferencesRequest = {
      browser_identity: cookie.identity,
      preferences: fidesUserPreferences,
      privacy_experience_id: experience.id,
      user_geography: userLocationString,
      method: consentMethod,
      ...(tcf ?? []),
    };
    await patchUserPreferenceToFidesServer(
      privacyPreferenceCreate,
      options.fidesApiUrl,
      options.debug
    );
  }
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
  servedNotices?: Array<LastServedConsentSchema> | null;
  tcf?: TcfSavePreferences;
  updateCookie: (oldCookie: FidesCookie) => Promise<FidesCookie>;
}) => {
  // 1. Update the cookie object based on new preferences
  const updatedCookie = await updateCookie(cookie);
  Object.assign(cookie, updatedCookie);

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
        userLocationString
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
  saveFidesCookie(cookie);

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
  dispatchFidesEvent("FidesUpdated", cookie, options.debug);
};
