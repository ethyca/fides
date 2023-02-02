export type Config = {
  title: string;
  description: string;
  server_url_development?: string;
  server_url_production?: string;
  logo_path: string;
  actions: PrivacyRequestOption[];
  includeConsent: boolean;
  consent?: {
    icon_path: string;
    title: string;
    description: string;
    identity_inputs?: Record<string, string>;
    policy_key?: string;
    consentOptions: ConfigConsentOption[];
  };
};

export type PrivacyRequestOption = {
  policy_key: string;
  icon_path: string;
  title: string;
  description: string;
  identity_inputs?: Record<string, string>;
};

export type ConfigConsentOption = {
  cookieKeys: string[];
  default?: boolean;
  description: string;
  fidesDataUseKey: string;
  highlight?: boolean;
  name: string;
  url: string;
  executable?: boolean;
};
