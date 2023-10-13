import { TCModel, TCString, Vector } from "@iabtechlabtcf/core";
import { PrivacyExperience } from "../consent-types";
import { EnabledIds, TcfCookieConsent, TcfCookieKeyConsent } from "./types";
import { TCF_KEY_MAP } from "./constants";
import { generateTcString } from "../tcf";
import { debugLog } from "../consent-utils";

export const transformTcStringToCookieKeys = (
  tcString: string,
  debug: boolean
): TcfCookieConsent => {
  const tcModel: TCModel = TCString.decode(tcString || "");

  const cookieKeys: TcfCookieConsent = {};

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
  debugLog(
    debug,
    `Generated cookie.tcf_consent from explicit tc string.`,
    cookieKeys
  );
  return cookieKeys;
};

export const generateTcStringFromCookieTcfConsent = async (
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
