import {
  ConsentMechanism, ConsentMethod,
  ConsentOptionCreate,
  PrivacyNotice,
  PrivacyPreferencesRequest,
  UserConsentPreference,
} from "./consent-types";
import { debugLog } from "./consent-utils";
import {
  CookieKeyConsent,
  getOrMakeFidesCookie,
  saveFidesCookie,
} from "./cookie";
import { patchUserPreferenceToFidesServer } from "../services/fides/api";

/**
 * Updates the user's consent preferences, going through the following steps:
 * 1. Save preferences to Fides API
 * 2. Update the window.Fides.consent object
 * 3. Save preferences to the `fides_consent` cookie in the browser
 */
export const updateConsentPreferences = ({
  privacyNotices,
  experienceHistoryId,
  enabledPrivacyNoticeIds,
  fidesApiUrl,
  consentMethod,
  userLocationString,
  debug = false,
}: {
  privacyNotices: PrivacyNotice[];
  experienceHistoryId: string;
  enabledPrivacyNoticeIds: Array<PrivacyNotice["id"]>;
  fidesApiUrl: String;
  consentMethod: ConsentMethod;
  userLocationString: string;
  debug?: boolean;
}) => {
  const cookie = getOrMakeFidesCookie();

  // Derive the CookieKeyConsent object from privacy notices
  const noticeMap = new Map<string, boolean>(
    privacyNotices.map((notice) => [
      // DEFER(fides#3281): use notice key
      notice.id,
      enabledPrivacyNoticeIds.includes(notice.id),
    ])
  );
  const consentCookieKey: CookieKeyConsent = Object.fromEntries(noticeMap);

  // Derive the Fides user preferences array from privacy notices
  const fidesUserPreferences: Array<ConsentOptionCreate> = [];
  privacyNotices.forEach((notice) => {
    let consentPreference;
    if (enabledPrivacyNoticeIds.includes(notice.id)) {
      if (notice.consent_mechanism === ConsentMechanism.NOTICE_ONLY) {
        consentPreference = UserConsentPreference.ACKNOWLEDGE;
      } else {
        consentPreference = UserConsentPreference.OPT_IN;
      }
    } else {
      consentPreference = UserConsentPreference.OPT_OUT;
    }
    fidesUserPreferences.push({
      privacy_notice_history_id: notice.privacy_notice_history_id,
      preference: consentPreference,
    });
  });

  // 1. Save preferences to Fides API
  debugLog(debug, "Saving preferences to Fides API");
  const privacyPreferenceCreate: PrivacyPreferencesRequest = {
    browser_identity: cookie.identity,
    preferences: fidesUserPreferences,
    privacy_experience_history_id: experienceHistoryId,
    user_geography: userLocationString,
    method: consentMethod
  };
  patchUserPreferenceToFidesServer(
      privacyPreferenceCreate,
      fidesApiUrl,
      cookie.identity.fides_user_device_id,
      debug
  );

  // 2. Update the window.Fides.consent object
  debugLog(debug, "Updating window.Fides");
  window.Fides.consent = consentCookieKey;

  // 3. Save preferences to the cookie
  debugLog(debug, "Saving preferences to cookie");
  saveFidesCookie({ ...cookie, consent: consentCookieKey });
};
