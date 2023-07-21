/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { Dataset } from "./Dataset";
import type { DatasetTraversalDetails } from "./DatasetTraversalDetails";

/**
 * Response model for validating a dataset, which includes both the dataset
 * itself (if valid) plus a details object describing if the dataset is
 * traversable or not.
 */
export type ValidateDatasetResponse = {
  dataset: Dataset;
  traversal_details: DatasetTraversalDetails;
};
