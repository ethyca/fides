export interface MultiselectFieldValue extends Array<string> {}

export interface FormValues
  extends Record<string, string | MultiselectFieldValue> {}

export interface CustomPrivacyRequestField {
  label: string;
  field_type: "text" | "select" | "multiselect";
  required?: boolean;
  options?: string[];
  default_value?: string | string[];
  hidden?: boolean;
  query_param_key?: string;
}

export interface CustomPrivacyRequestFields {
  [key: string]: CustomPrivacyRequestField;
}
