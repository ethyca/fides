import {
  ConsentMethod,
  ConsentOptionCreate,
  LastServedConsentSchema,
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
 * Updates the user's consent preferences, going through the following steps:
 * 1. Save preferences to Fides API
 * 2. Update the window.Fides.consent object
 * 3. Save preferences to the `fides_consent` cookie in the browser
 * 4. Remove any cookies from notices that were opted-out from the browser
 * 5. Dispatch a "FidesUpdated" event
 */
export const updateConsentPreferences = async ({
  consentPreferencesToSave,
  experienceId,
  fidesApiUrl,
  consentMethod,
  fidesDisableSaveApi,
  userLocationString,
  cookie,
  debug = false,
  servedNotices,
  tcf,
  updateCookie,
}: {
  consentPreferencesToSave?: Array<SaveConsentPreference>;
  experienceId: string;
  fidesApiUrl: string;
  consentMethod: ConsentMethod;
  fidesDisableSaveApi: boolean;
  userLocationString?: string;
  cookie: FidesCookie;
  debug?: boolean;
  servedNotices?: Array<LastServedConsentSchema> | null;
  tcf?: TcfSavePreferences;
  updateCookie: (oldCookie: FidesCookie) => Promise<FidesCookie>;
}) => {
  // Derive the Fides user preferences array from privacy notices
  const fidesUserPreferences: Array<ConsentOptionCreate> | undefined =
    consentPreferencesToSave
      ? consentPreferencesToSave.map(({ notice, consentPreference }) => {
          const servedNotice = servedNotices
            ? servedNotices.find(
                (n) =>
                  n.privacy_notice_history?.id ===
                  notice.privacy_notice_history_id
              )
            : undefined;
          return {
            privacy_notice_history_id: notice.privacy_notice_history_id,
            preference: consentPreference,
            served_notice_history_id: servedNotice?.served_notice_history_id,
          };
        })
      : undefined;

  // 1. Save preferences to Fides API
  if (!fidesDisableSaveApi) {
    debugLog(debug, "Saving preferences to Fides API");
    const privacyPreferenceCreate: PrivacyPreferencesRequest = {
      browser_identity: cookie.identity,
      preferences: fidesUserPreferences,
      privacy_experience_id: experienceId,
      user_geography: userLocationString,
      method: consentMethod,
      ...(tcf ?? []),
    };
    patchUserPreferenceToFidesServer(
      privacyPreferenceCreate,
      fidesApiUrl,
      debug
    );
  }

  // 2. Update the cookie object based on new preferences
  const updatedCookie = await updateCookie(cookie);
  Object.assign(cookie, updatedCookie);

  // 3. Update the window.Fides object
  debugLog(debug, "Updating window.Fides");
  window.Fides.consent = cookie.consent;
  window.Fides.fides_string = cookie.fides_string;
  window.Fides.tcf_consent = cookie.tcf_consent;

  // 4. Save preferences to the cookie in the browser
  debugLog(debug, "Saving preferences to cookie");
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
  dispatchFidesEvent("FidesUpdated", cookie, debug);
};
