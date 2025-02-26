/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { Location } from "./Location";
import type { LocationGroup } from "./LocationGroup";
import type { LocationRegulationBase } from "./LocationRegulationBase";

export type LocationRegulationResponse = {
  locations?: Array<Location>;
  location_groups?: Array<LocationGroup>;
  regulations?: Array<LocationRegulationBase>;
};
