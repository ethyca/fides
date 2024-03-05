/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { PropertyType } from "./PropertyType";

/**
 * A base template for all other Fides Schemas to inherit from.
 */
export type Property = {
  name: string;
  type: PropertyType;
  key?: string;
};
