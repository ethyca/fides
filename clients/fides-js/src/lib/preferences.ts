import {
  ConsentMethod,
  ConsentOptionCreate,
  LastServedNoticeSchema, PrivacyExperience,
  PrivacyPreferencesRequest,
  SaveConsentPreference,
  UserConsentPreference,
} from "./consent-types";
import { debugLog, transformUserPreferenceToBoolean } from "./consent-utils";
import {
  CookieKeyConsent,
  FidesCookie,
  removeCookiesFromBrowser,
  saveFidesCookie,
} from "./cookie";
import { dispatchFidesEvent } from "./events";
import { patchUserPreferenceToFidesServer } from "../services/fides/api";
import {TcfSavePreferences, TcStringPreferences} from "./tcf/types";
import {buildTcStringPreferences} from "./tcf/tcf";

/**
 * Updates the user's consent preferences, going through the following steps:
 * 1. Save preferences to Fides API
 * 2. Update the window.Fides.consent object
 * 3. Save preferences to the `fides_consent` cookie in the browser
 * 4. Remove any cookies from notices that were opted-out from the browser
 * 5. Dispatch a "FidesUpdated" event
 */
export const updateConsentPreferences = ({
  consentPreferencesToSave,
  experience,
  fidesApiUrl,
  consentMethod,
  userLocationString,
  cookie,
  debug = false,
  servedNotices,
  tcf,
}: {
  consentPreferencesToSave: Array<SaveConsentPreference>;
  experience: PrivacyExperience;
  fidesApiUrl: string;
  consentMethod: ConsentMethod;
  userLocationString?: string;
  cookie: FidesCookie;
  debug?: boolean;
  servedNotices?: Array<LastServedNoticeSchema> | null;
  tcf?: TcfSavePreferences;
}) => {
  // Derive the CookieKeyConsent object from privacy notices
  const noticeMap = new Map<string, boolean>(
    consentPreferencesToSave.map(({ notice, consentPreference }) => [
      notice.notice_key,
      transformUserPreferenceToBoolean(consentPreference),
    ])
  );
  const consentCookieKey: CookieKeyConsent = Object.fromEntries(noticeMap);

  // Derive the Fides user preferences array from privacy notices
  const fidesUserPreferences: Array<ConsentOptionCreate> =
    consentPreferencesToSave.map(({ notice, consentPreference }) => {
      const servedNotice = servedNotices
        ? servedNotices.find(
            (n) =>
              n.privacy_notice_history.id === notice.privacy_notice_history_id
          )
        : undefined;
      return {
        privacy_notice_history_id: notice.privacy_notice_history_id,
        preference: consentPreference,
        served_notice_history_id: servedNotice?.served_notice_history_id,
      };
    });

  // Update the cookie object
  // eslint-disable-next-line no-param-reassign
  cookie.consent = consentCookieKey;

  // 1. Save preferences to Fides API
  debugLog(debug, "Saving preferences to Fides API");
  const privacyPreferenceCreate: PrivacyPreferencesRequest = {
    browser_identity: cookie.identity,
    preferences: fidesUserPreferences,
    privacy_experience_id: experience.id,
    user_geography: userLocationString,
    method: consentMethod,
    ...(tcf ?? []),
  };
  patchUserPreferenceToFidesServer(privacyPreferenceCreate, fidesApiUrl, debug);

  // 2. Update the window.Fides.consent object
  debugLog(debug, "Updating window.Fides");
  window.Fides.consent = cookie.consent;

  // 3. TCF
  let tcStringPreferences: TcStringPreferences;
  // Instead of making a new call for user prefs, this manually adds the new tcf preferences to existing experience
  // tcf data in the effort of reducing roundtrip calls to Fides server for performance
  if (tcf) {
    console.log(experience)
    // At this point, this obj contains just experience data, restructured
    tcStringPreferences = buildTcStringPreferences(experience)
    console.log("tc string tcf purposes...")
    console.log(tcStringPreferences?.tcf_purposes)
    console.log(tcStringPreferences?.tcf_purposes?.get(6))
    console.log(tcStringPreferences?.tcf_purposes?.get(6)?.current_preference)
    // "Upsert" new tcf preferences to existing experience data
    tcf.purpose_preferences?.forEach(purpose => {
      // @ts-ignore
      // todo- map preference to current_preference
      tcStringPreferences.tcf_purposes.get(purpose.id) = tcStringPreferences.tcf_purposesget(purpose.id) || {}
      tcStringPreferences.tcf_purposes.get(purpose.id).current_preference = purpose.preference
    })
    tcf.special_purpose_preferences?.forEach(purpose => {
      // @ts-ignore
      tcStringPreferences.tcf_special_purposes[purpose.id] = purpose
    })
    tcf.vendor_preferences?.forEach(purpose => {
      // @ts-ignore
      tcStringPreferences.tcf_vendors[purpose.id] = purpose
    })
    tcf.feature_preferences?.forEach(purpose => {
      // @ts-ignore
      tcStringPreferences.tcf_features[purpose.id] = purpose
    })
    tcf.special_feature_preferences?.forEach(purpose => {
      // @ts-ignore
      tcStringPreferences.tcf_special_features[purpose.id] = purpose
    })
    // Update the cookie object with TCF prefs
    // eslint-disable-next-line no-param-reassign
    cookie.tcStringPreferences = tcStringPreferences
  }

  // 4. Save preferences to the cookie
  debugLog(debug, "Saving preferences to cookie");
  saveFidesCookie(cookie);

  // 5. Remove cookies associated with notices that were opted-out from the browser
  consentPreferencesToSave
    .filter(
      (preference) =>
        preference.consentPreference === UserConsentPreference.OPT_OUT
    )
    .forEach((preference) => {
      removeCookiesFromBrowser(preference.notice.cookies);
    });

  // 6. Dispatch a "FidesUpdated" event
  dispatchFidesEvent("FidesUpdated", cookie, debug);
};
