/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { FidesDatasetReference } from "./FidesDatasetReference";

/**
 * A named variable which can be sourced from identities, dataset references, or connector params. These values
 * are used to replace the placeholders in the path, header, query, and body param values.
 */
export type ParamValue = {
  name: string;
  identity?: string;
  references?: Array<FidesDatasetReference | string>;
  connector_param?: string;
  unpack?: boolean;
};
