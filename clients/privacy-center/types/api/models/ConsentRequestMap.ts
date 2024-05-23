/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { SaaSRequest } from "./SaaSRequest";

/**
 * A map of actions to Consent requests
 */
export type ConsentRequestMap = {
  opt_in?: SaaSRequest | Array<SaaSRequest>;
  opt_out?: SaaSRequest | Array<SaaSRequest>;
};
