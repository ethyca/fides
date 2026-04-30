import { UploadFile } from "fidesui";

export interface MultiselectFieldValue extends Array<string> {}

export type FormFieldValue = string | string[] | boolean | UploadFile[];

// FormValues uses Record<string, any> to accommodate legacy string fields,
// multiselect arrays, checkbox booleans, and file upload arrays.
// Use FormFieldValue for type-safe access to individual field values.
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export interface FormValues extends Record<string, any> {}

export interface CustomPrivacyRequestField {
  label: string;
  field_type?:
    | "text"
    | "select"
    | "multiselect"
    | "checkbox"
    | "checkbox_group"
    | "textarea"
    | "file"
    | "location";
  required?: boolean;
  options?: string[];
  default_value?: string | string[];
  hidden?: boolean;
  query_param_key?: string;
  ip_geolocation_hint?: boolean;
  max_size_bytes?: number;
  allowed_mime_types?: string[];
}

export interface CustomPrivacyRequestFields {
  [key: string]: CustomPrivacyRequestField;
}
