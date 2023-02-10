/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { DrpAction } from "./DrpAction";

/**
 * An external representation of a Fidesops Policy
 */
export type fides__api__ops__schemas__policy__Policy = {
  name: string;
  key?: string;
  drp_action?: DrpAction;
  execution_timeframe?: number;
};
