import { ConsentValue } from "fides-js";

export type IdentityInputs = {
  name?: string;
  email?: string;
  phone?: string;
};

export type LegacyConfig = {
  title: string;
  description: string;
  description_subtext?: string[];
  addendum?: string[];
  server_url_development?: string;
  server_url_production?: string;
  logo_path: string;
  actions: PrivacyRequestOption[];
  includeConsent?: boolean;
  consent?: LegacyConsentConfig | ConsentConfig;
};

export type Config = {
  title: string;
  description: string;
  description_subtext?: string[];
  addendum?: string[];
  server_url_development?: string;
  server_url_production?: string;
  logo_path: string;
  actions: PrivacyRequestOption[];
  includeConsent?: boolean;
  consent?: ConsentConfig;
};

export type LegacyConsentConfig = {
  icon_path: string;
  title: string;
  description: string;
  identity_inputs?: IdentityInputs;
  policy_key?: string;
  consentOptions: ConfigConsentOption[];
};

export type ConsentConfig = {
  button: {
    description: string;
    icon_path: string;
    identity_inputs?: IdentityInputs;
    title: string;
  };
  page: {
    consentOptions: ConfigConsentOption[];
    description: string;
    description_subtext?: string[];
    policy_key?: string;
    title: string;
  };
};

export type PrivacyRequestOption = {
  policy_key: string;
  icon_path: string;
  title: string;
  description: string;
  identity_inputs?: IdentityInputs;
};

export type ConfigConsentOption = {
  cookieKeys: string[];
  default?: ConsentValue;
  description: string;
  fidesDataUseKey: string;
  highlight?: boolean;
  name: string;
  url: string;
  executable?: boolean;
};
