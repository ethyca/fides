import { ConfigConsentOption } from "~/config/types";

import { ConsentItem, ApiUserConsents, ApiUserConsent } from "./types";

export const makeConsentItems = (
  data: ApiUserConsents,
  consentOptions: ConfigConsentOption[]
) => {
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
          highlight: d.highlight,
          name: d.name,
          url: d.url,
        });
      } else {
        newConsentItems.push({
          fidesDataUseKey: d.fidesDataUseKey,
          name: d.name,
          description: d.description,
          highlight: d.highlight,
          url: d.url,
          defaultValue: d.default ? d.default : false,
        });
      }
    });

    return newConsentItems;
  }

  const temp = consentOptions.map((option) => ({
    fidesDataUseKey: option.fidesDataUseKey,
    name: option.name,
    description: option.description,
    highlight: option.highlight,
    url: option.url,
    defaultValue: option.default ? option.default : false,
  }));
  return temp;
};
