/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { Dataset_Output } from "./Dataset_Output";
import type { DatasetTraversalDetails } from "./DatasetTraversalDetails";

/**
 * Response model for validating a dataset, which includes both the dataset
 * itself (if valid) plus a details object describing if the dataset is
 * traversable or not.
 */
export type ValidateDatasetResponse = {
  dataset: Dataset_Output;
  traversal_details: DatasetTraversalDetails;
};
