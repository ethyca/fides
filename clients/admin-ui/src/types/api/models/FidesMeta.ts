/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { FidesDatasetReference } from "./FidesDatasetReference";
import type { FieldMaskingStrategyOverride } from "./FieldMaskingStrategyOverride";

/**
 * Supplementary metadata used by the Fides application for additional features.
 */
export type FidesMeta = {
  /**
   * Fields that current field references or is referenced by. Used for drawing the edges of a DSR graph.
   */
  references?: Array<FidesDatasetReference> | null;
  /**
   * The type of the identity data that should be used to query this collection for a DSR.
   */
  identity?: string | null;
  /**
   * Whether the current field can be considered a primary key of the current collection
   */
  primary_key?: boolean | null;
  /**
   * Optionally specify the data type. Fides will attempt to cast values to this type when querying.
   */
  data_type?: string | null;
  /**
   * Optionally specify the allowable field length. Fides will not generate values that exceed this size.
   */
  length?: number | null;
  /**
   * Optionally specify to query for the entire array if the array is an entrypoint into the node. Default is False.
   */
  return_all_elements?: boolean | null;
  /**
   * Optionally specify if a field is read-only, meaning it can't be updated or deleted.
   */
  read_only?: boolean | null;
  /**
   * Optionally specify that a field may be used as a custom request field in DSRs. The value is the name of the field in the DSR.
   */
  custom_request_field?: string | null;
  /**
   * Optionally specify a masking strategy override for this field.
   */
  masking_strategy_override?: FieldMaskingStrategyOverride | null;
};
