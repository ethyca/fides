import { ConsentContext } from "./consent-context";
import {
  ConsentMechanism,
  ConsentValue,
  NoticeConsent,
  PrivacyNoticeWithPreference,
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
  context: ConsentContext,
  consent: NoticeConsent | undefined,
): boolean => {
  if (notice.consent_mechanism === ConsentMechanism.NOTICE_ONLY) {
    return true;
  }
  // Note about GPC - consent has already applied to the cookie at this point, so we can trust preference there
  // DEFER (PROD-1780): delete context arg for safety
  if (consent && noticeHasConsentInCookie(notice, consent)) {
    return !!consent[notice.notice_key];
  }

  return transformUserPreferenceToBoolean(notice.default_preference);
};
