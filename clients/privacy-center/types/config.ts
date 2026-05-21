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

// Display condition types — mirrors the backend's Condition schema but restricted
// to the 5 operators allowed for display_condition on custom fields.
export type DisplayOperator =
  | "eq"
  | "neq"
  | "exists"
  | "not_exists"
  | "list_contains";

export type DisplayGroupOperator = "and" | "or";

export interface ConditionLeaf {
  field_address: string;
  operator: DisplayOperator;
  value?: string | number | boolean | Array<string | number | boolean> | null;
}

export interface ConditionGroup {
  logical_operator: DisplayGroupOperator;
  conditions: Array<ConditionLeaf | ConditionGroup>;
}

export type Condition = ConditionLeaf | ConditionGroup;

export interface ICustomField {
  label: string;
  required?: boolean;
  query_param_key?: string | null;
  hidden?: boolean;
  placeholder?: string;
  display_condition?: Condition | null;
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

export interface CustomCheckboxField extends ICustomField {
  default_value?: string | null;
  field_type: "checkbox";
}

export interface CustomCheckboxGroupField extends ICustomField {
  default_value?: string[] | null;
  field_type: "checkbox_group";
  options: string[];
}

export interface CustomTextareaField extends ICustomField {
  default_value?: string | null;
  field_type: "textarea";
}

export interface CustomFileUploadField extends ICustomField {
  default_value?: string | null;
  field_type: "file";
  max_size_bytes?: number;
  max_file_count?: number;
  allowed_file_types?: string[];
}

export interface CustomLocationField extends ICustomField {
  default_value?: string | null;
  field_type: "location";
  options?: string[];
  ip_geolocation_hint?: boolean;
}

export interface CustomDateField extends ICustomField {
  default_value?: string | null;
  field_type: "date";
  min?: string | null; // ISO 8601 date string (YYYY-MM-DD)
  max?: string | null; // ISO 8601 date string (YYYY-MM-DD)
}

export type CustomConfigField =
  | CustomTextField
  | CustomSelectField
  | CustomMultiSelectField
  | CustomCheckboxField
  | CustomCheckboxGroupField
  | CustomTextareaField
  | CustomFileUploadField
  | CustomLocationField
  | CustomDateField;
export type CustomIdentityField =
  | CustomTextField
  | CustomSelectField
  | CustomDateField
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
  error_message?: string | null;
};

export type MetricsConfig = {
  title?: string;
  description?: string;
  link_text?: string;
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
  // Unified render order across identity_inputs and custom_privacy_request_fields.
  // When set, the renderer iterates this list strictly and looks each key up in
  // either bucket. Absent on legacy configs — those fall back to the hardcoded
  // name → email → phone → other identities → customs sequence.
  field_order?: string[] | null;
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
