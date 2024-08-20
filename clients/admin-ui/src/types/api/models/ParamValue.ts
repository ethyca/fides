/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * A named variable which can be sourced from identities, dataset references, or connector params. These values
 * are used to replace the placeholders in the path, header, query, and body param values.
 */
export type ParamValue = {
  name: string;
  identity?: string | null;
  references?: null;
  connector_param?: string | null;
  unpack?: boolean | null;
};
