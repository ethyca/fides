/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { SaaSRequestMap } from "./SaaSRequestMap";

/**
 * A collection of read/update/delete requests which corresponds to a FidesDataset collection (by name)
 */
export type Endpoint = {
  name: string;
  requests: SaaSRequestMap;
  skip_processing?: boolean;
  after?: Array<string>;
  erase_after?: Array<string>;
};
