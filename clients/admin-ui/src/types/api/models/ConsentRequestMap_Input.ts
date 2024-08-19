/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { SaaSRequest_Input } from "./SaaSRequest_Input";

/**
 * A map of actions to Consent requests
 */
export type ConsentRequestMap_Input = {
  opt_in?: SaaSRequest_Input | Array<SaaSRequest_Input>;
  opt_out?: SaaSRequest_Input | Array<SaaSRequest_Input>;
};
