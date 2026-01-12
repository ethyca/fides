import {
  ConsentMechanism,
  NoticeConsent,
  PrivacyNotice,
  PrivacyNoticeWithPreference,
  SaveConsentPreference,
  UserConsentPreference,
} from "./consent-types";
import { selectBestNoticeTranslation } from "./i18n";

// Privacy Center cannot import consent-utils.ts due to Webpack build issue.
// We separate out utils shared by fides-js and privacy-center here.

/**
 * Returns true if notice has a corresponding key in cookie. This means a user has a consent val for that notice.
 * Assumes that cookie has not been overridden with other consent vals prior to being called.
 */
export const noticeHasConsentInCookie = (
  notice: PrivacyNoticeWithPreference,
  consent: NoticeConsent,
): boolean => Boolean(Object.keys(consent).includes(notice.notice_key));
/**
 * Convert a user consent preference into true/false
 */
export const transformUserPreferenceToBoolean = (
  preference: UserConsentPreference | undefined,
) => {
  if (!preference) {
    return false;
  }
  if (preference === UserConsentPreference.OPT_OUT) {
    return false;
  }
  if (preference === UserConsentPreference.OPT_IN) {
    return true;
  }
  return preference === UserConsentPreference.ACKNOWLEDGE;
};
/**
 * Convert a true/false consent to Fides user consent preference
 */
export const transformConsentToFidesUserPreference = (
  consented: boolean,
  consentMechanism?: ConsentMechanism,
): UserConsentPreference => {
  if (consented) {
    if (consentMechanism === ConsentMechanism.NOTICE_ONLY) {
      return UserConsentPreference.ACKNOWLEDGE;
    }
    return UserConsentPreference.OPT_IN;
  }
  return UserConsentPreference.OPT_OUT;
};

/**
 * Builds an array of SaveConsentPreference objects from a notice consent map.
 * This utility handles the common pattern of:
 * 1. Looking up notices by key
 * 2. Finding the best translation for each notice
 * 3. Converting boolean/enum preferences to UserConsentPreference
 * 4. Creating SaveConsentPreference objects with history IDs
 *
 * @param noticeConsent - Map of notice keys to consent values (boolean or UserConsentPreference)
 * @param privacyNotices - Array of privacy notices to process
 * @param locale - Current locale for translation selection
 * @param defaultLocale - Fallback locale if current locale translation not found
 * @param fullObjects - If true, returns full SaveConsentPreference objects; if false, returns minimal objects with just noticeHistoryId and consentPreference
 * @returns Array of SaveConsentPreference objects (or minimal versions)
 */
export const buildConsentPreferencesArray = <T extends boolean = true>(
  noticeConsent: NoticeConsent,
  privacyNotices: PrivacyNotice[],
  locale: string,
  defaultLocale: string,
  fullObjects?: T,
): T extends true
  ? SaveConsentPreference[]
  : Array<
      Pick<SaveConsentPreference, "noticeHistoryId" | "consentPreference">
    > => {
  const consentPreferencesToSave: SaveConsentPreference[] = [];

  privacyNotices.forEach((notice) => {
    const preference = noticeConsent[notice.notice_key];

    if (preference !== undefined) {
      const bestTranslation = selectBestNoticeTranslation(
        locale,
        defaultLocale,
        notice,
      );
      const historyId = bestTranslation?.privacy_notice_history_id;

      if (historyId) {
        // Convert preference to boolean if needed, then to UserConsentPreference
        let consentPreference: UserConsentPreference;
        if (typeof preference === "boolean") {
          consentPreference = transformConsentToFidesUserPreference(
            preference,
            notice.consent_mechanism,
          );
        } else {
          // It's already a UserConsentPreference, but we may need to normalize it
          const booleanPreference =
            transformUserPreferenceToBoolean(preference);
          consentPreference = transformConsentToFidesUserPreference(
            booleanPreference,
            notice.consent_mechanism,
          );
        }

        if (fullObjects !== false) {
          consentPreferencesToSave.push(
            new SaveConsentPreference(notice, consentPreference, historyId),
          );
        } else {
          consentPreferencesToSave.push({
            noticeHistoryId: historyId,
            consentPreference,
          } as SaveConsentPreference);
        }
      }
    }
  });

  return consentPreferencesToSave as any;
};

/**
 * Used to process consent values from externally accessible sources (Cookie, Events, Fides.consent)
 * If the experience is set to use consent mechanism as the consent value, we need to transform the
 * value to a boolean for internal use.
 *
 * Type-checks a consent value and transforms it if it's a string.
 * If the value is a string, it converts it to a boolean using transformUserPreferenceToBoolean.
 * Otherwise, returns the original value.
 *
 * @param value - The ambiguous consent value to process.
 * @returns The processed consent value as a boolean for internal use.
 */
export const processExternalConsentValue = (
  value: boolean | UserConsentPreference,
): boolean => {
  if (typeof value === "string") {
    return transformUserPreferenceToBoolean(value);
  }
  return value;
};

/**
 * Parses a comma-separated string of notice keys into an array of strings.
 * Handles undefined input, trims whitespace, and filters out empty strings.
 */
export const parseCommaSeparatedString = (
  value: string | undefined,
): string[] => {
  if (!value) {
    return [];
  }

  return value
    .split(",")
    .map((key) => key.trim())
    .filter(Boolean);
};
