/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { FidesDatasetReference } from "./FidesDatasetReference";

/**
 * Supplementary metadata used by the Fides application for additional features.
 */
export type FidesMeta = {
  /**
   * Fields that current field references or is referenced by. Used for drawing the edges of a DSR graph.
   */
  references?: Array<FidesDatasetReference>;
  /**
   * The type of the identity data that should be used to query this collection for a DSR.
   */
  identity?: string;
  /**
   * Whether the current field can be considered a primary key of the current collection
   */
  primary_key?: boolean;
  /**
   * Optionally specify the data type. Fides will attempt to cast values to this type when querying.
   */
  data_type?: string;
  /**
   * Optionally specify the allowable field length. Fides will not generate values that exceed this size.
   */
  length?: number;
  /**
   * Optionally specify to query for the entire array if the array is an entrypoint into the node. Default is False.
   */
  return_all_elements?: boolean;
  /**
   * Optionally specify if a field is read-only, meaning it can't be updated or deleted.
   */
  read_only?: boolean;
};
