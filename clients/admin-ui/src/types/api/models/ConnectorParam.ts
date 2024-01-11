/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Used to define the required parameters for the connector (user and constants)
 */
export type ConnectorParam = {
  name: string;
  label?: string;
  options?: Array<string>;
  default_value?: Array<string> | string;
  multiselect?: boolean;
  description?: string;
  sensitive?: boolean;
};
