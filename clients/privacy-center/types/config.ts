import { ConfigConsentOption } from "./api";

type LegacyIdentityConfigProps = "optional" | "required" | string | null;

type DefaultIdentities = {
  name?: LegacyIdentityConfigProps; // here for legacy purposes, we don't treat it as an identity or pass it along in the privacy request
  email?: LegacyIdentityConfigProps;
  phone?: LegacyIdentityConfigProps;
};

export type DefaultIdentityKeys = keyof DefaultIdentities;

export type CustomIdentityFields = Record<
  string,
  CustomConfigField | LegacyIdentityConfigProps
>;

export type IdentityInputs = DefaultIdentities & CustomIdentityFields;

export interface ICustomField {
  label: string;
  required?: boolean;
  query_param_key?: string | null;
  hidden?: boolean;
}

export interface CustomTextField extends ICustomField {
  default_value?: string | null;
  field_type?: "text" | null;
}

export interface CustomSelectField extends ICustomField {
  default_value?: string | null;
  field_type: "select";
  options?: string[];
}

export interface CustomMultiSelectField extends ICustomField {
  default_value?: string[] | null;
  field_type: "multiselect";
  options?: string[];
}

export interface CustomLocationField extends ICustomField {
  default_value?: string | null;
  field_type: "location";
  options?: string[];
  ip_geolocation_hint?: boolean;
}

export type CustomConfigField =
  | CustomTextField
  | CustomSelectField
  | CustomMultiSelectField
  | CustomLocationField;
export type CustomIdentityField =
  | CustomTextField
  | CustomSelectField
  | (CustomLocationField & {
      required: true;
    });

export type CustomPrivacyRequestFields = Record<string, CustomConfigField>;

export type LegacyConfig = {
  title: string;
  description: string;
  description_subtext?: string[];
  addendum?: string[];
  server_url_development?: string;
  server_url_production?: string;
  logo_path: string;
  actions?: PrivacyRequestOption[];
  includeConsent?: boolean;
  consent?: LegacyConsentConfig | ConsentConfig;
};

export type MetricsConfig = {
  title?: string;
  description?: string;
  link_text?: string;
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
  page_title?: string;
  actions?: PrivacyRequestOption[];
  includeConsent?: boolean;
  consent?: ConsentConfig;
  /** @deprecated Prefer `links`. Kept for backwards compatibility. */
  privacy_policy_url?: string;
  /** @deprecated Prefer `links`. Kept for backwards compatibility. */
  privacy_policy_url_text?: string;
  links?: PrivacyCenterLink[];
  metrics?: MetricsConfig;
};

export type PrivacyCenterLink = {
  label: string;
  url: string;
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
  description_subtext?: string[] | null;
  confirmButtonText?: string | null;
  cancelButtonText?: string | null;
  identity_inputs?: IdentityInputs | null;
  custom_privacy_request_fields?: CustomPrivacyRequestFields | null;
  verification_title?: string | null;
  verification_description?: string | null;
  verification_submit_button_text?: string | null;
  verification_resend_button_text?: string | null;
  success_title?: string | null;
  success_description?: string | null;
  success_button_text?: string | null;
};

export enum ConsentNonApplicableFlagMode {
  OMIT = "omit",
  INCLUDE = "include",
}

export enum ConsentFlagType {
  BOOLEAN = "boolean",
  CONSENT_MECHANISM = "consent_mechanism",
}
