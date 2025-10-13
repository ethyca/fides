import { ConsentContext } from "./consent-context";
import {
  ConsentMechanism,
  ConsentValue,
  NoticeConsent,
  PrivacyNoticeWithPreference,
  UserConsentPreference,
} from "./consent-types";
import {
  noticeHasConsentInCookie,
  transformUserPreferenceToBoolean,
} from "./shared-consent-utils";

export const resolveLegacyConsentValue = (
  value: ConsentValue | undefined,
  context: ConsentContext,
): boolean => {
  if (value === undefined) {
    return false;
  }

  if (typeof value === "boolean") {
    return value;
  }

  if (context.globalPrivacyControl === true) {
    return value.globalPrivacyControl;
  }

  return value.value;
};

export const resolveConsentValue = (
  notice: PrivacyNoticeWithPreference,
  consent: NoticeConsent | undefined,
): boolean => {
  if (notice.consent_mechanism === ConsentMechanism.NOTICE_ONLY) {
    return true;
  }
  if (consent && noticeHasConsentInCookie(notice, consent)) {
    if (typeof consent[notice.notice_key] === "string") {
      return transformUserPreferenceToBoolean(
        consent[notice.notice_key] as UserConsentPreference,
      );
    }
    return consent[notice.notice_key] as boolean;
  }

  return transformUserPreferenceToBoolean(notice.default_preference);
};
