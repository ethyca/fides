/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { DrpAction } from "./DrpAction";

/**
 * Drp data rights response
 */
export type DrpDataRightsResponse = {
  version: string;
  api_base?: string | null;
  actions: Array<DrpAction>;
  user_relationships?: Array<string> | null;
};
