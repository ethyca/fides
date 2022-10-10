import config from "./config.json";

export type Config = typeof config;
export type ConfigConsentOption = Config["consent"]["consentOptions"][number];
