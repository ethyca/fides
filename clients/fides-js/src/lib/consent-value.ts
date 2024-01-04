import { ConsentContext } from "./consent-context";
import {
  ConsentMechanism,
  ConsentValue,
  FidesCookie,
  PrivacyNoticeWithPreference,
} from "./consent-types";
import {
  noticeHasConsentInCookie,
  transformUserPreferenceToBoolean,
} from "./consent-utils";

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
  cookie: FidesCookie
): boolean => {
  if (notice.consent_mechanism === ConsentMechanism.NOTICE_ONLY) {
    return true;
  }
  const preferenceExistsInCookie = noticeHasConsentInCookie(notice, cookie);
  // Note about GPC - consent has already applied to the cookie at this point, so we can trust preference there
  if (preferenceExistsInCookie) {
    return <boolean>cookie.consent[notice.notice_key];
  }
  return transformUserPreferenceToBoolean(notice.default_preference);
};
