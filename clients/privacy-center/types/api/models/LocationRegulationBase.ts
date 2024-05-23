/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { Continent } from "./Continent";

/**
 * Base Location Regulation Schema
 */
export type LocationRegulationBase = {
  id: string;
  selected?: boolean;
  name: string;
  continent: Continent;
  default_selected?: boolean;
};
