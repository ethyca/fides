/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ReadSaaSRequest } from "./ReadSaaSRequest";
import type { SaaSRequest } from "./SaaSRequest";

/**
 * A map of actions to SaaS requests
 */
export type SaaSRequestMap = {
  read?: ReadSaaSRequest | Array<ReadSaaSRequest>;
  update?: SaaSRequest | null;
  delete?: SaaSRequest | null;
};
