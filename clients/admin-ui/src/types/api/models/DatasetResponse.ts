/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { DatasetCollection } from "./DatasetCollection";
import type { DatasetMetadata } from "./DatasetMetadata";

/**
 * Dataset response model for API endpoints.
 *
 * Note: This class extends the Dataset model from fideslang rather than having a proper
 * dedicated API response model. We had to make the collections field
 * Optional and allow null values to support the minimal=true parameter in API responses,
 * even though collections is required in the base fideslang Dataset model.
 */
export type DatasetResponse = {
  /**
   * A unique key used to identify this resource.
   */
  fides_key: string;
  /**
   * Defines the Organization that this resource belongs to.
   */
  organization_fides_key?: string;
  tags?: Array<string> | null;
  /**
   * Human-Readable name for this resource.
   */
  name?: string | null;
  /**
   * A detailed description of what this resource is.
   */
  description?: string | null;
  /**
   * An optional property to store any extra information for a resource. Data can be structured in any way: simple set of `key: value` pairs or deeply nested objects.
   */
  meta?: null;
  /**
   * Array of Data Category resources identified by `fides_key`, that apply to all collections in the Dataset.
   */
  data_categories?: Array<string> | null;
  /**
   *
   * The DatasetMetadata resource model.
   *
   * Object used to hold application specific metadata for a dataset
   *
   */
  fides_meta?: DatasetMetadata | null;
  /**
   * An array of objects that describe the Dataset's collections.
   */
  collections?: Array<DatasetCollection> | null;
};
