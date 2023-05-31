import { ConsentContext } from "./consent-context";
import { ConsentValue, UserConsentPreference } from "./consent-types";
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
  value: UserConsentPreference,
  context: ConsentContext,
  current_preference?: UserConsentPreference | null,
  has_gpc_flag?: boolean
): boolean => {
  if (current_preference) {
    return transformUserPreferenceToBoolean(current_preference);
  }
  const gpcEnabled = !!has_gpc_flag && context.globalPrivacyControl === true;
  if (gpcEnabled) {
    return false;
  }

  return transformUserPreferenceToBoolean(value);
};
