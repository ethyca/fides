/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Location field that doesn't support options and includes IP geolocation hint
 */
export type LocationCustomPrivacyRequestField = {
  label: string;
  required?: (boolean | null);
  default_value?: (string | null);
  hidden?: (boolean | null);
  query_param_key?: (string | null);
  field_type?: LocationCustomPrivacyRequestField.field_type;
  ip_geolocation_hint?: (boolean | null);
};

export namespace LocationCustomPrivacyRequestField {

  export enum field_type {
    LOCATION = 'location',
  }


}

