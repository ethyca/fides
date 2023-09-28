import { PrivacyExperience } from "../consent-types";
import { EnabledIds, TcfCookieConsent, TcfCookieKeyConsent } from "./types";
import { TCF_KEY_MAP } from "./constants";
import { generateTcString } from "../tcf";

export const generateTcStringFromCookieTcfConsent = async (
  experience: PrivacyExperience,
  tcfConsent: TcfCookieConsent
): Promise<string> => {
  const enabledIds: any | EnabledIds = {
    purposesConsent: [],
    purposesLegint: [],
    specialPurposes: [],
    features: [],
    specialFeatures: [],
    vendorsConsent: [],
    vendorsLegint: [],
  };

  TCF_KEY_MAP.forEach(({ cookieKey, enabledIdsKey }) => {
    if (cookieKey) {
      const cookieKeyConsent: TcfCookieKeyConsent | undefined =
        tcfConsent[cookieKey];
      if (cookieKeyConsent) {
        Object.keys(cookieKeyConsent).forEach((key: string | number) => {
          if (cookieKeyConsent[key] && enabledIdsKey) {
            enabledIds[enabledIdsKey].push(key.toString());
          }
        });
      }
    }
  });
  return generateTcString({
    experience,
    tcStringPreferences: enabledIds,
  });
};
