import { TCModel, TCString, Vector } from "@iabtechlabtcf/core";
import { PrivacyExperience } from "../consent-types";
import { EnabledIds, TcfCookieConsent, TcfCookieKeyConsent } from "./types";
import { TCF_KEY_MAP } from "./constants";
import { generateFidesString } from "../tcf";
import { debugLog } from "../consent-utils";

export const transformFidesStringToCookieKeys = (
  fidesString: string,
  debug: boolean
): TcfCookieConsent => {
  // Defer: to fully support AC string, we need to split out TC from AC string https://github.com/ethyca/fides/issues/4263
  const tcString = (fidesString || "").split(",")[0];
  const tcModel: TCModel = TCString.decode(tcString);

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
    `Generated cookie.tcf_consent from explicit fidesString.`,
    cookieKeys
  );
  return cookieKeys;
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
