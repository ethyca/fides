/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ReadSaaSRequest_Output } from "./ReadSaaSRequest_Output";
import type { SaaSRequest_Output } from "./SaaSRequest_Output";

/**
 * A map of actions to SaaS requests
 */
export type SaaSRequestMap_Output = {
  read?: ReadSaaSRequest_Output | Array<ReadSaaSRequest_Output>;
  update?: SaaSRequest_Output | null;
  delete?: SaaSRequest_Output | null;
};
