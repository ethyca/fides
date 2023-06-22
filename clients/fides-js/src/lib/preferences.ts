import {
  ConsentMethod,
  ConsentOptionCreate,
  PrivacyPreferencesRequest,
  SaveConsentPreference,
} from "./consent-types";
import { debugLog, transformUserPreferenceToBoolean } from "./consent-utils";
import { CookieKeyConsent, FidesCookie, saveFidesCookie } from "./cookie";
import { dispatchFidesEvent } from "./events";
import { patchUserPreferenceToFidesServer } from "../services/fides/api";

/**
 * Updates the user's consent preferences, going through the following steps:
 * 1. Save preferences to Fides API
 * 2. Update the window.Fides.consent object
 * 3. Save preferences to the `fides_consent` cookie in the browser
 */
export const updateConsentPreferences = ({
  consentPreferencesToSave,
  experienceId,
  fidesApiUrl,
  consentMethod,
  userLocationString,
  cookie,
  debug = false,
}: {
  consentPreferencesToSave: Array<SaveConsentPreference>;
  experienceId: string;
  fidesApiUrl: string;
  consentMethod: ConsentMethod;
  userLocationString?: string;
  cookie: FidesCookie;
  debug?: boolean;
}) => {
  // Derive the CookieKeyConsent object from privacy notices
  const noticeMap = new Map<string, boolean>(
    consentPreferencesToSave.map(({ noticeKey, consentPreference }) => [
      noticeKey,
      transformUserPreferenceToBoolean(consentPreference),
    ])
  );
  const consentCookieKey: CookieKeyConsent = Object.fromEntries(noticeMap);

  // Derive the Fides user preferences array from privacy notices
  const fidesUserPreferences: Array<ConsentOptionCreate> = [];
  consentPreferencesToSave.forEach(({ noticeHistoryId, consentPreference }) => {
    fidesUserPreferences.push({
      privacy_notice_history_id: noticeHistoryId,
      preference: consentPreference,
    });
  });

  // Update the cookie object
  // eslint-disable-next-line no-param-reassign
  cookie.consent = consentCookieKey;

  // 1. Save preferences to Fides API
  debugLog(debug, "Saving preferences to Fides API");
  const privacyPreferenceCreate: PrivacyPreferencesRequest = {
    browser_identity: cookie.identity,
    preferences: fidesUserPreferences,
    privacy_experience_id: experienceId,
    user_geography: userLocationString,
    method: consentMethod,
  };
  patchUserPreferenceToFidesServer(
    privacyPreferenceCreate,
    fidesApiUrl,
    cookie.identity.fides_user_device_id,
    debug
  );

  // 2. Update the window.Fides.consent object
  debugLog(debug, "Updating window.Fides");
  window.Fides.consent = cookie.consent;

  // 3. Save preferences to the cookie
  debugLog(debug, "Saving preferences to cookie");
  saveFidesCookie(cookie);

  // 4. Dispatch a "FidesUpdated" event
  dispatchFidesEvent("FidesUpdated", cookie, debug);
};
