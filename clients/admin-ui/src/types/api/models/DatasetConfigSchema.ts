/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { Dataset_Output } from "./Dataset_Output";

/**
 * Returns the DatasetConfig fides key and the linked Ctl Dataset
 */
export type DatasetConfigSchema = {
  fides_key: string;
  ctl_dataset: Dataset_Output;
};
