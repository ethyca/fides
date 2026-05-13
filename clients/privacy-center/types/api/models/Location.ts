/* istanbul ignore file */
/* tslint:disable */

import type { Continent } from "./Continent";

/**
 * Location schema
 */
export type Location = {
  id: string;
  selected?: boolean;
  name: string;
  continent: Continent;
  default_selected?: boolean;
  belongs_to?: Array<string>;
  regulation?: Array<string>;
};
