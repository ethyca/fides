import { ConsentContext } from "./consent-context";
import {
  ConsentMechanism,
  ConsentValue,
  CookieKeyConsent,
  PrivacyNoticeWithPreference,
} from "./consent-types";
import {
  noticeHasConsentInCookie,
  transformUserPreferenceToBoolean,
} from "./shared-consent-utils";

export const resolveLegacyConsentValue = (
  value: ConsentValue | undefined,
  context: ConsentContext
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
  consent: CookieKeyConsent | undefined
): boolean => {
  if (notice.consent_mechanism === ConsentMechanism.NOTICE_ONLY) {
    return true;
  }
  // Note about GPC - consent has already applied to the cookie at this point, so we can trust preference there
  // TODO (PROD-1780): this is probably not true anymore...!
  if (consent && noticeHasConsentInCookie(notice, consent)) {
    return !!consent[notice.notice_key];
  }

  return transformUserPreferenceToBoolean(notice.default_preference);
};
