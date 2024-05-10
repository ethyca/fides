/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { Location } from "./Location";
import type { LocationGroup } from "./LocationGroup";
import type { LocationRegulationBase } from "./LocationRegulationBase";

/**
 * A base template for all other Fides Schemas to inherit from.
 */
export type LocationRegulationResponse = {
  locations?: Array<Location>;
  location_groups?: Array<LocationGroup>;
  regulations?: Array<LocationRegulationBase>;
};
