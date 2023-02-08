import {
  ConsentContext,
  CookieKeyConsent,
  resolveConsentValue,
} from "fides-consent";

import { ConfigConsentOption } from "~/types/config";
import { FidesKeyToConsent } from "./types";

export const makeCookieKeyConsent = ({
  consentOptions,
  fidesKeyToConsent,
  consentContext,
}: {
  consentOptions: ConfigConsentOption[];
  fidesKeyToConsent: FidesKeyToConsent;
  consentContext: ConsentContext;
}): CookieKeyConsent => {
  const cookieKeyConsent: CookieKeyConsent = {};
  consentOptions.forEach((option) => {
    const defaultValue = resolveConsentValue(option.default, consentContext);
    const value = fidesKeyToConsent[option.fidesDataUseKey] ?? defaultValue;

    option.cookieKeys?.forEach((cookieKey) => {
      const previousConsent = cookieKeyConsent[cookieKey];
      // For a cookie key to have consent, _all_ data uses that target that cookie key
      // must have consent.
      cookieKeyConsent[cookieKey] =
        previousConsent === undefined ? value : previousConsent && value;
    });
  });
  return cookieKeyConsent;
};
