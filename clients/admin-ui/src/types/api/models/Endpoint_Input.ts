/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { SaaSRequestMap_Input } from "./SaaSRequestMap_Input";

/**
 * A collection of read/update/delete requests which corresponds to a FidesDataset collection (by name)
 */
export type Endpoint_Input = {
  name: string;
  requests: SaaSRequestMap_Input;
  skip_processing?: boolean;
  after?: Array<string>;
  erase_after?: Array<string>;
};
