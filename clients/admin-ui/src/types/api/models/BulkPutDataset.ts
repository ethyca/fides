/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { BulkUpdateFailed } from "./BulkUpdateFailed";
import type { Dataset } from "./Dataset";

export type DatasetFieldWarning = {
  collection?: string;
  field?: string;
  message: string;
};

/**
 * Schema with mixed success/failure responses for Bulk Create/Update of Datasets.
 */
export type BulkPutDataset = {
  succeeded: Array<Dataset>;
  failed: Array<BulkUpdateFailed>;
  warnings?: Array<DatasetFieldWarning>;
};
