/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ReadSaaSRequest_Input } from "./ReadSaaSRequest_Input";
import type { SaaSRequest_Input } from "./SaaSRequest_Input";

/**
 * A map of actions to SaaS requests
 */
export type SaaSRequestMap_Input = {
  read?: ReadSaaSRequest_Input | Array<ReadSaaSRequest_Input>;
  update?: SaaSRequest_Input | null;
  delete?: SaaSRequest_Input | null;
};
