/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { CollectionMeta } from "./CollectionMeta";
import type { DatasetField } from "./DatasetField";

/**
 * The DatasetCollection resource model.
 *
 * This resource is nested within a Dataset.
 */
export type DatasetCollection = {
  /**
   * Human-Readable name for this resource.
   */
  name: string;
  /**
   * A detailed description of what this resource is.
   */
  description?: string | null;
  /**
   * Array of Data Category resources identified by `fides_key`, that apply to all fields in the collection.
   */
  data_categories?: Array<string> | null;
  /**
   * An array of objects that describe the collection's fields.
   */
  fields: Array<DatasetField>;
  fides_meta?: CollectionMeta | null;
};
