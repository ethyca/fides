/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { Strategy } from "./Strategy";

/**
 * Definition for an authenticated base HTTP client
 */
export type ClientConfig = {
  protocol: string;
  host: string;
  authentication?: Strategy | null;
};
