/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { Continent } from "./Continent";

/**
 * Location Group schema, currently the same as a location
 */
export type LocationGroup = {
  id: string;
  selected?: boolean;
  name: string;
  continent: Continent;
  default_selected?: boolean;
  belongs_to?: Array<string>;
  regulation?: Array<string>;
  is_country?: boolean;
};
