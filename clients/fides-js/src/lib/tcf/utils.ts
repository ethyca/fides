import { TCModel, TCString, Vector } from "@iabtechlabtcf/core";
import { PrivacyExperience } from "../consent-types";
import { EnabledIds, TcfCookieConsent, TcfCookieKeyConsent } from "./types";
import { TCF_KEY_MAP } from "./constants";
import { generateFidesString } from "../tcf";
import { debugLog } from "../consent-utils";
import { decodeFidesString, idsFromAcString } from "./fidesString";

export const transformFidesStringToCookieKeys = (
  fidesString: string,
  debug: boolean
): { cookieKeys: TcfCookieConsent; success: boolean } => {
  const { tc: tcString, ac: acString } = decodeFidesString(fidesString);
  const cookieKeys: TcfCookieConsent = {};
  try {
    const tcModel: TCModel = TCString.decode(tcString);
    // map tc model key to cookie key
    TCF_KEY_MAP.forEach(({ tcfModelKey, cookieKey }) => {
      if (tcfModelKey) {
        const items: TcfCookieKeyConsent = {};
        (tcModel[tcfModelKey] as Vector).forEach((consented, id) => {
          items[id] = consented;
        });
        cookieKeys[cookieKey] = items;
      }
    });

    // Set AC consents, which will only be on vendor_consents
    const acIds = idsFromAcString(acString, debug);
    acIds.forEach((acId) => {
      if (!cookieKeys.vendor_consent_preferences) {
        cookieKeys.vendor_consent_preferences = { [acId]: true };
      } else {
        cookieKeys.vendor_consent_preferences[acId] = true;
      }
    });
    debugLog(
      debug,
      `Generated cookie.tcf_consent from explicit fidesString.`,
      cookieKeys
    );
    return { cookieKeys, success: true };
  } catch (error) {
    debugLog(
      debug,
      `Could not decode tcString ${tcString}, it may be invalid. ${error}`
    );
    return { cookieKeys, success: false };
  }
};

export const generateFidesStringFromCookieTcfConsent = async (
  experience: PrivacyExperience,
  tcfConsent: TcfCookieConsent
): Promise<string> => {
  const enabledIds: EnabledIds = {
    purposesConsent: [],
    purposesLegint: [],
    specialPurposes: [],
    features: [],
    specialFeatures: [],
    vendorsConsent: [],
    vendorsLegint: [],
  };

  TCF_KEY_MAP.forEach(({ cookieKey, enabledIdsKey }) => {
    const cookieKeyConsent: TcfCookieKeyConsent | undefined =
      tcfConsent[cookieKey];
    if (cookieKeyConsent) {
      Object.keys(cookieKeyConsent).forEach((key: string | number) => {
        if (cookieKeyConsent[key] && enabledIdsKey) {
          enabledIds[enabledIdsKey].push(key.toString());
        }
      });
    }
  });
  return generateFidesString({
    experience,
    tcStringPreferences: enabledIds,
  });
};
