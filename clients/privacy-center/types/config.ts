import { ConsentValue } from "fides-consent";

export type IdentityInputs = {
  name?: string;
  email?: string;
  phone?: string;
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
  consent?: {
    icon_path: string;
    title: string;
    description: string;
    description_subtext?: string[];
    identity_inputs?: IdentityInputs;
    policy_key?: string;
    consentOptions: ConfigConsentOption[];
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
