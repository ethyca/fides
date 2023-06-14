import { ConsentContext } from "./consent-context";
import { ConsentValue, PrivacyNotice } from "./consent-types";
import { transformUserPreferenceToBoolean } from "./consent-utils";

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
  notice: PrivacyNotice,
  context: ConsentContext
): boolean => {
  if (notice.current_preference) {
    return transformUserPreferenceToBoolean(notice.current_preference);
  }
  const gpcEnabled =
    !!notice.has_gpc_flag && context.globalPrivacyControl === true;
  if (gpcEnabled) {
    return false;
  }

  return transformUserPreferenceToBoolean(notice.default_preference);
};
