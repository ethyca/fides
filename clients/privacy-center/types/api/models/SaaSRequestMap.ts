/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { SaaSRequest } from "./SaaSRequest";

/**
 * A map of actions to SaaS requests
 */
export type SaaSRequestMap = {
  read?: SaaSRequest | Array<SaaSRequest>;
  update?: SaaSRequest;
  delete?: SaaSRequest;
};
