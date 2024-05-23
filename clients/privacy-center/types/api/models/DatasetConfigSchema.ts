/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { Dataset } from "./Dataset";

/**
 * Returns the DatasetConfig fides key and the linked Ctl Dataset
 */
export type DatasetConfigSchema = {
  fides_key: string;
  ctl_dataset: Dataset;
};
