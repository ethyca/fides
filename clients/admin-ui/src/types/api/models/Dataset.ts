/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ContactDetails } from "./ContactDetails";
import type { DatasetCollection } from "./DatasetCollection";
import type { DatasetMetadata } from "./DatasetMetadata";

/**
 * The Dataset resource model.
 */
export type Dataset = {
  /**
   * A unique key used to identify this resource.
   */
  fides_key: string;
  /**
   * Defines the Organization that this resource belongs to.
   */
  organization_fides_key?: string;
  tags?: Array<string>;
  /**
   * Human-Readable name for this resource.
   */
  name?: string;
  /**
   * A detailed description of what this resource is.
   */
  description?: string;
  /**
   * An optional property to store any extra information for a resource. Data can be structured in any way: simple set of `key: value` pairs or deeply nested objects.
   */
  meta?: any;
  /**
   * Array of Data Category resources identified by `fides_key`, that apply to all collections in the Dataset.
   */
  data_categories?: Array<string>;
  /**
   *
   * The DatasetMetadata resource model.
   *
   * Object used to hold application specific metadata for a dataset
   *
   */
  fides_meta?: DatasetMetadata;
  /**
   * Deprecated.
   * The contact details information model.
   *
   * Used to capture contact information for controllers, used
   * as part of exporting a data map / ROPA.
   *
   * This model is nested under an Organization and
   * potentially under a system/dataset.
   *
   */
  joint_controller?: ContactDetails;
  /**
   * Deprecated. An optional string to describe the retention policy for a dataset. This field can also be applied more granularly at either the Collection or field level of a Dataset.
   */
  retention?: string;
  /**
   * Deprecated. An optional array to identify any third countries where data is transited to. For consistency purposes, these fields are required to follow the Alpha-3 code set in [ISO 3166-1](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-3).
   */
  third_country_transfers?: Array<string>;
  /**
   * An array of objects that describe the Dataset's collections.
   */
  collections: Array<DatasetCollection>;
};
