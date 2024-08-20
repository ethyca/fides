/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { FidesMeta } from "./FidesMeta";

/**
 * The DatasetField resource model.
 *
 * This resource is nested within a DatasetCollection.
 */
export type DatasetField = {
  /**
   * Human-Readable name for this resource.
   */
  name: string;
  /**
   * A detailed description of what this resource is.
   */
  description?: string | null;
  /**
   * Arrays of Data Categories, identified by `fides_key`, that applies to this field.
   */
  data_categories?: Array<string> | null;
  fides_meta?: FidesMeta | null;
  /**
   * An optional array of objects that describe hierarchical/nested fields (typically found in NoSQL databases).
   */
  fields?: Array<DatasetField> | null;
};
