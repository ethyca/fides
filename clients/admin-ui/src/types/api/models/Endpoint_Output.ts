/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { SaaSRequestMap_Output } from "./SaaSRequestMap_Output";

/**
 * A collection of read/update/delete requests which corresponds to a FidesDataset collection (by name)
 */
export type Endpoint_Output = {
  name: string;
  requests: SaaSRequestMap_Output;
  skip_processing?: boolean;
  after?: Array<string>;
  erase_after?: Array<string>;
};
