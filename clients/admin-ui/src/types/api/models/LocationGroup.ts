/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { Continent } from './Continent';

/**
 * Used to represent location groups in API responses.
 *
 * Only differs from a Location in that it has no `selected`
 * field.
 */
export type LocationGroup = {
  id: string;
  name: string;
  continent: Continent;
  belongs_to?: Array<string>;
};

