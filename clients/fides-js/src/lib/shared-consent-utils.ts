import {
  ConsentMechanism,
  NoticeConsent,
  PrivacyNoticeWithPreference,
  UserConsentPreference,
} from "./consent-types";

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
export const parseFidesDisabledNotices = (
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
