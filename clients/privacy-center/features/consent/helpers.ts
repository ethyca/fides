import {
  ConsentContext,
  GpcStatus,
  NoticeConsent,
  resolveLegacyConsentValue,
} from "fides-js";

import { ConfigConsentOption } from "~/types/api";
import { ConsentConfig, LegacyConsentConfig } from "~/types/config";

import { FidesKeyToConsent } from "./types";

/**
 * Ascertain whether a consentConfig is V1 or V2 based upon the presence of a `button` key
 */
export function isV1ConsentConfig(
  consentConfig: LegacyConsentConfig | ConsentConfig | undefined,
): consentConfig is LegacyConsentConfig {
  return (
    typeof consentConfig === "object" &&
    consentConfig != null &&
    !("button" in consentConfig)
  );
}

/**
 * A method to translate the original version (v1) of the Fides Privacy Center config
 * into the semantically improved version (v2) which separates the page and button
 * data.
 */
export const translateV1ConfigToV2 = ({
  v1ConsentConfig,
}: {
  v1ConsentConfig: LegacyConsentConfig;
}): ConsentConfig => ({
  button: {
    icon_path: v1ConsentConfig.icon_path,
    description: v1ConsentConfig.description,
    identity_inputs: v1ConsentConfig.identity_inputs,
    title: v1ConsentConfig.title,
  },
  page: {
    consentOptions: v1ConsentConfig.consentOptions,
    description: v1ConsentConfig.description,
    description_subtext: [],
    policy_key: v1ConsentConfig.policy_key,
    title: v1ConsentConfig.title,
  },
});

export const makeNoticeConsent = ({
  consentOptions,
  fidesKeyToConsent,
  consentContext,
}: {
  consentOptions: ConfigConsentOption[];
  fidesKeyToConsent: FidesKeyToConsent;
  consentContext: ConsentContext;
}): NoticeConsent => {
  const consent: NoticeConsent = {};
  consentOptions.forEach((option) => {
    const defaultValue = resolveLegacyConsentValue(
      option.default!,
      consentContext,
    );
    const value = fidesKeyToConsent[option.fidesDataUseKey] ?? defaultValue;

    option.cookieKeys?.forEach((cookieKey) => {
      const previousConsent = consent[cookieKey];
      // For a cookie key to have consent, _all_ data uses that target that cookie key
      // must have consent. E.g. if previous consent is false, keep false, else if true, we use new value
      consent[cookieKey] =
        previousConsent === undefined ? value : previousConsent && value;
    });
  });
  return consent;
};

export const getGpcStatus = ({
  value,
  consentOption,
  consentContext,
}: {
  value: boolean;
  consentOption: ConfigConsentOption;
  consentContext: ConsentContext;
}): GpcStatus => {
  // If GPC is not enabled, it won't be applied at all.
  if (!consentContext.globalPrivacyControl) {
    return GpcStatus.NONE;
  }
  // Options that are plain booleans apply without considering GPC.
  if (typeof consentOption.default !== "object") {
    return GpcStatus.NONE;
  }

  if (value === consentOption.default?.globalPrivacyControl) {
    return GpcStatus.APPLIED;
  }

  return GpcStatus.OVERRIDDEN;
};
