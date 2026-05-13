/* istanbul ignore file */
/* tslint:disable */

import type { CollectionAddressResponse } from "./CollectionAddressResponse";

/**
 * Response model for dataset dry run
 */
export type DryRunDatasetResponse = {
  collectionAddress: CollectionAddressResponse;
  query: any;
};
