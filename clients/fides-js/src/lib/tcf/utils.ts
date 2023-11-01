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
): TcfCookieConsent => {
  const { tc: tcString, ac: acString } = decodeFidesString(fidesString);
  const tcModel: TCModel = TCString.decode(tcString);

  const cookieKeys: TcfCookieConsent = {};

  // map tc model key to cookie key
  TCF_KEY_MAP.forEach(({ tcfModelKey, cookieKey }) => {
    const isVendorKey =
      tcfModelKey === "vendorConsents" ||
      tcfModelKey === "vendorLegitimateInterests";
    if (tcfModelKey) {
      const items: TcfCookieKeyConsent = {};
      (tcModel[tcfModelKey] as Vector).forEach((consented, id) => {
        const key = isVendorKey ? `gvl.${id}` : id;
        items[key] = consented;
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
