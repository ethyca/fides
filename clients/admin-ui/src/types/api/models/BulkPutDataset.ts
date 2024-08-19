/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { BulkUpdateFailed } from "./BulkUpdateFailed";
import type { Dataset_Output } from "./Dataset_Output";

/**
 * Schema with mixed success/failure responses for Bulk Create/Update of Datasets.
 */
export type BulkPutDataset = {
  succeeded: Array<Dataset_Output>;
  failed: Array<BulkUpdateFailed>;
};
