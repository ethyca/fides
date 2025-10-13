/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Regular custom privacy request field supporting text, select, and multiselect types
 */
export type fides__api__schemas__privacy_center_config__CustomPrivacyRequestField = {
  label: string;
  required?: (boolean | null);
  default_value?: (string | null);
  hidden?: (boolean | null);
  query_param_key?: (string | null);
  field_type?: ('text' | 'select' | 'multiselect' | null);
  options?: (Array<string> | null);
};

