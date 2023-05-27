import {
  ConsentMechanism,
  ConsentOptionCreate,
  PrivacyNotice,
  PrivacyPreferencesCreateWithCode,
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
  enabledPrivacyNoticeIds,
  debug = false,
}: {
  privacyNotices: PrivacyNotice[];
  enabledPrivacyNoticeIds: Array<PrivacyNotice["id"]>;
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

  // 1. DEFER: Save preferences to Fides API
  debugLog(debug, "Saving preferences to Fides API");
  const privacyPreferenceCreate: PrivacyPreferencesCreateWithCode = {
    browser_identity: cookie.identity,
    preferences: fidesUserPreferences,
  };
  patchUserPreferenceToFidesServer(privacyPreferenceCreate, debug);

  // 2. Update the window.Fides.consent object
  debugLog(debug, "Updating window.Fides");
  window.Fides.consent = consentCookieKey;

  // 3. Save preferences to the cookie
  debugLog(debug, "Saving preferences to cookie");
  saveFidesCookie({ ...cookie, consent: consentCookieKey });
};
