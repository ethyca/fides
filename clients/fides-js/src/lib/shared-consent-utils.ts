import { ConsentFlagType } from "~/integrations/gtm";

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

type NoticeConsentMechanismMap = {
  [key: string]: ConsentMechanism;
};

interface BaseNormalizeConsentValuesOptions {
  consent: NoticeConsent;
}

interface BooleanConsentOptions extends BaseNormalizeConsentValuesOptions {
  flagType?: ConsentFlagType.BOOLEAN;
  consentMechanisms?: NoticeConsentMechanismMap;
}

interface ConsentMechanismOptions extends BaseNormalizeConsentValuesOptions {
  flagType: ConsentFlagType.CONSENT_MECHANISM;
  consentMechanisms: NoticeConsentMechanismMap;
}

type NormalizeConsentValuesOptions =
  | BooleanConsentOptions
  | ConsentMechanismOptions;

/**
 * Normalizes consent values between boolean and consent mechanism formats.
 * For boolean format: converts consent mechanism strings to booleans
 * For consent mechanism format: converts booleans to consent mechanism strings
 * @param consent - The consent values to normalize
 * @param flagType - The target format for normalization
 * @param consentMechanisms - Required when converting booleans to consent mechanisms
 */
export const normalizeConsentValues = ({
  consent,
  flagType = ConsentFlagType.BOOLEAN,
  consentMechanisms,
}: NormalizeConsentValuesOptions): NoticeConsent => {
  const normalizedConsentValues: NoticeConsent = {};

  // For boolean case, we need to transform any consent mechanism strings to booleans
  if (flagType !== ConsentFlagType.CONSENT_MECHANISM) {
    Object.keys(consent).forEach((key) => {
      const value = consent[key];
      if (typeof value === "string") {
        // Transform consent mechanism strings to booleans
        normalizedConsentValues[key] = transformUserPreferenceToBoolean(
          value as UserConsentPreference,
        );
      } else {
        normalizedConsentValues[key] = value;
      }
    });
    return normalizedConsentValues;
  }

  // For consent mechanism case, we need the consent mechanisms to transform booleans
  const hasBooleanValues = Object.values(consent).some(
    (value) => typeof value === "boolean",
  );
  if (hasBooleanValues && !consentMechanisms) {
    throw new Error(
      "Cannot transform boolean consent values to consent mechanisms without consent mechanisms map",
    );
  }

  // If no boolean values, return as is
  if (!hasBooleanValues) {
    return { ...consent };
  }

  Object.keys(consent).forEach((key) => {
    const value = consent[key];
    if (typeof value === "string") {
      normalizedConsentValues[key] = value;
    } else {
      const consentMechanism = (consentMechanisms as NoticeConsentMechanismMap)[
        key
      ];
      normalizedConsentValues[key] = transformConsentToFidesUserPreference(
        value,
        consentMechanism,
      );
    }
  });

  return normalizedConsentValues;
};
