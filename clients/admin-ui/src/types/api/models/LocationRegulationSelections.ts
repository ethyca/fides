/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { Selection } from "./Selection";

/**
 * A base template for all other Fides Schemas to inherit from.
 */
export type LocationRegulationSelections = {
  locations?: Array<Selection>;
  regulations?: Array<Selection>;
};
