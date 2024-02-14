/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { Continent } from './Continent';

/**
 * A base template for all other Fides Schemas to inherit from.
 */
export type Location = {
  id: string;
  selected?: boolean;
  name: string;
  continent: Continent;
  belongs_to?: Array<string>;
  regulation?: Array<string>;
};

