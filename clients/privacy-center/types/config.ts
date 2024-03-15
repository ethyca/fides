import { ConsentValue } from "fides-js";

export type IdentityInputs = {
  name?: string;
  email?: string;
  phone?: string;
};

export type CustomPrivacyRequestFields = Record<
  string,
  {
    label: string;
    required?: boolean;
    default_value?: string;
    hidden?: boolean;
  }
>;

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
  logo_url?: string;
  favicon_path?: string;
  actions: PrivacyRequestOption[];
  includeConsent?: boolean;
  consent?: ConsentConfig;
  privacy_policy_url?: string;
  privacy_policy_url_text?: string;
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
    description_subtext?: string[];
    confirmButtonText?: string;
    cancelButtonText?: string;
    icon_path: string;
    identity_inputs?: IdentityInputs;
    custom_privacy_request_fields?: CustomPrivacyRequestFields;
    title: string;
    modalTitle?: string;
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
  description_subtext?: string[];
  confirmButtonText?: string;
  cancelButtonText?: string;
  identity_inputs?: IdentityInputs;
  custom_privacy_request_fields?: CustomPrivacyRequestFields;
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
