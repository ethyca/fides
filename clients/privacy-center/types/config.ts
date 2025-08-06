import { ConfigConsentOption } from "./api";

type DefaultIdentities = {
  name?: string | null; // here for legacy purposes, we don't treat it as an identity or pass it along in the privacy request
  email?: string | null;
  phone?: string | null;
  location?: LocationIdentityField | null;
};

export type CustomIdentity = {
  label: string;
};

export type LocationIdentityField = {
  label: string;
  required?: boolean;
  default_value?: string;
  query_param_key?: string;
  ip_geolocation_hint?: boolean;
};

export type IdentityInputs = DefaultIdentities &
  (Record<string, CustomIdentity> | object);

export type CustomPrivacyRequestFields = Record<
  string,
  {
    label: string;
    required?: boolean;
    default_value?: string | string[];
    query_param_key?: string;
    hidden?: boolean;
    field_type?: "text" | "multiselect" | "select";
    options?: string[];
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

export type LocationCollectionConfig = {
  collection: "required" | "optional";
  ip_geolocation_hint: boolean;
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
  location?: LocationCollectionConfig;
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

export enum ConsentNonApplicableFlagMode {
  OMIT = "omit",
  INCLUDE = "include",
}

export enum ConsentFlagType {
  BOOLEAN = "boolean",
  CONSENT_MECHANISM = "consent_mechanism",
}
