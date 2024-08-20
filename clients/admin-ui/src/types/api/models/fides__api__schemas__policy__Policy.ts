/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { DrpAction } from "./DrpAction";

/**
 * An external representation of a Fidesops Policy
 */
export type fides__api__schemas__policy__Policy = {
  name: string;
  key?: string | null;
  drp_action?: DrpAction | null;
  execution_timeframe?: number | null;
};
