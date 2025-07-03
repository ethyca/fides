/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ManualFieldSystem } from "./ManualFieldSystem";
import type { ManualFieldUser } from "./ManualFieldUser";

/**
 * Optional filter dropdown values returned alongside the result set.
 */
export type ManualFieldSearchFilterOptions = {
  assigned_users?: Array<ManualFieldUser>;
  systems?: Array<ManualFieldSystem>;
};
