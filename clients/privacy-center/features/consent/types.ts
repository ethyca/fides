export type ConsentItem = {
  fidesDataUseKey: string;
  name: string;
  description: string;
  highlight: boolean;
  url: string;
  defaultValue: boolean;
  consentValue?: boolean;
  cookieKeys?: string[];
  executable?: boolean;
};

export type ApiUserConsent = {
  data_use: string;
  data_use_description?: string;
  opt_in: boolean;
};

export type ApiUserConsents = {
  consent?: ApiUserConsent[];
};
