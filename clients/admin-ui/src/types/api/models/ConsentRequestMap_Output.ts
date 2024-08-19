/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { SaaSRequest_Output } from "./SaaSRequest_Output";

/**
 * A map of actions to Consent requests
 */
export type ConsentRequestMap_Output = {
  opt_in?: SaaSRequest_Output | Array<SaaSRequest_Output>;
  opt_out?: SaaSRequest_Output | Array<SaaSRequest_Output>;
};
