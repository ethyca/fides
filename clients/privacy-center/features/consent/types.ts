export type ConsentItem = {
  fidesDataUseKey: string;
  name: string;
  description: string;
  highlight: boolean;
  url: string;
  defaultValue: boolean;
  consentValue?: boolean;
  cookieKeys: string[];
};

export type ApiUserConsent = {
  data_use: string;
  data_use_description?: string;
  opt_in: boolean;
};

export type ApiUserConsents = {
  consent?: ApiUserConsent[];
};

/**
 * A mapping from the cookie keys (defined in config.json) to the resolved consent value.
 */
export type CookieKeyConsent = {
  [cookieKey: string]: boolean | undefined;
};
