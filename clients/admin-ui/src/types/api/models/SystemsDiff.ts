/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { System_Output } from "./System_Output";

/**
 * A schema representing the diff between the scan and saved systems
 */
export type SystemsDiff = {
  added_ingress: Record<string, Array<string>>;
  added_egress: Record<string, Array<string>>;
  removed_ingress: Record<string, Array<string>>;
  removed_egress: Record<string, Array<string>>;
  added_systems: Array<System_Output>;
  removed_systems: Array<System_Output>;
};
