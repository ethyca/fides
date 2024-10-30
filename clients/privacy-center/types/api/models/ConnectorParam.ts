/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Used to define the required parameters for the connector (user and constants)
 */
export type ConnectorParam = {
  name: string;
  label?: string | null;
  options?: Array<string> | null;
  default_value?: string | Array<string> | number | Array<number> | null;
  multiselect?: boolean | null;
  description?: string | null;
  sensitive?: boolean | null;
};
