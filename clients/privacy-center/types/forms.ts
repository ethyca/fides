export interface MultiselectFieldValue extends Array<string> { }

export interface FormValues
  extends Record<string, string | MultiselectFieldValue> { }

export interface CustomPrivacyRequestField {
  label: string;
  field_type?: "text" | "select" | "multiselect" | "location";
  required?: boolean;
  options?: string[];
  default_value?: string | string[];
  hidden?: boolean;
  query_param_key?: string;
  ip_geolocation_hint?: boolean;
}

export interface CustomPrivacyRequestFields {
  [key: string]: CustomPrivacyRequestField;
}
