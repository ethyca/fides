import {
  ConsentMechanism,
  NoticeConsent,
  PrivacyNoticeWithPreference,
  UserConsentPreference,
} from "./consent-types";

// PC cannot import consent-utils.ts due to Webpack build issue.
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
