import { PrivacyNotice } from "./consent-types";
import { debugLog } from "./consent-utils";
import {
  CookieKeyConsent,
  getOrMakeFidesCookie,
  saveFidesCookie,
} from "./cookie";

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
  // Derive the CookieKeyConsent object from privacy notices
  const noticeMap = new Map<string, boolean>(
    privacyNotices.map((notice) => [
      // DEFER(fides#3281): use notice key
      notice.id,
      enabledPrivacyNoticeIds.includes(notice.id),
    ])
  );
  const consentCookieKey: CookieKeyConsent = Object.fromEntries(noticeMap);

  // 1. DEFER: Save preferences to Fides API
  debugLog(debug, "Saving preferences to Fides API");

  // 2. Update the window.Fides.consent object
  debugLog(debug, "Updating window.Fides");
  // window.Fides.consent = consentCookieKey;

  // 3. Save preferences to the cookie
  debugLog(debug, "Saving preferences to cookie");
  const cookie = getOrMakeFidesCookie();
  saveFidesCookie({ ...cookie, consent: consentCookieKey });
};
