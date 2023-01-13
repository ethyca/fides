import { CookieKeyConsent } from "fides-consent";
import { ConfigConsentOption } from "~/types/config";

import { ConsentItem, ApiUserConsents, ApiUserConsent } from "./types";

export const makeConsentItems = (
  data: ApiUserConsents,
  consentOptions: ConfigConsentOption[]
): ConsentItem[] => {
  if (data.consent) {
    const newConsentItems: ConsentItem[] = [];
    const userConsentMap: { [key: string]: ApiUserConsent } = {};
    data.consent.forEach((option) => {
      const key = option.data_use;
      userConsentMap[key] = option;
    });
    consentOptions.forEach((d) => {
      if (d.fidesDataUseKey in userConsentMap) {
        const currentConsent = userConsentMap[d.fidesDataUseKey];

        newConsentItems.push({
          consentValue: currentConsent.opt_in,
          defaultValue: d.default ? d.default : false,
          description: currentConsent.data_use_description
            ? currentConsent.data_use_description
            : d.description,
          fidesDataUseKey: currentConsent.data_use,
          highlight: d.highlight ?? false,
          name: d.name,
          url: d.url,
          cookieKeys: d.cookieKeys ?? [],
          executable: d.executable ?? false,
        });
      } else {
        newConsentItems.push({
          fidesDataUseKey: d.fidesDataUseKey,
          name: d.name,
          description: d.description,
          highlight: d.highlight ?? false,
          url: d.url,
          defaultValue: d.default ? d.default : false,
          cookieKeys: d.cookieKeys ?? [],
          executable: d.executable ?? false,
        });
      }
    });

    return newConsentItems;
  }

  return consentOptions.map((option) => ({
    fidesDataUseKey: option.fidesDataUseKey,
    name: option.name,
    description: option.description,
    highlight: option.highlight ?? false,
    url: option.url,
    defaultValue: option.default ? option.default : false,
    cookieKeys: option.cookieKeys ?? [],
    executable: option.executable ?? false,
  }));
};

export const makeCookieKeyConsent = (
  consentItems: ConsentItem[]
): CookieKeyConsent => {
  const cookieKeyConsent: CookieKeyConsent = {};
  consentItems.forEach((item) => {
    const consent =
      item.consentValue === undefined ? item.defaultValue : item.consentValue;

    item.cookieKeys?.forEach((cookieKey) => {
      const previousConsent = cookieKeyConsent[cookieKey];
      cookieKeyConsent[cookieKey] =
        previousConsent === undefined ? consent : previousConsent && consent;
    });
  });
  return cookieKeyConsent;
};
