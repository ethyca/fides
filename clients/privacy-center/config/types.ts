import config from "./config.json";

export type Config = typeof config;

export type ConfigConsentOption = {
  cookieKeys: string[];
  default?: boolean;
  description: string;
  fidesDataUseKey: string;
  highlight?: boolean;
  name: string;
  url: string;
};
