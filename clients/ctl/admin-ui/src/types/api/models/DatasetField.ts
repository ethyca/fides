/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

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
  description?: string;
  /**
   * Arrays of Data Categories, identified by `fides_key`, that applies to this field.
   */
  data_categories?: Array<string>;
  /**
   * A Data Qualifier that applies to this field. Note that this field holds a single value, therefore, the property name is singular.
   */
  data_qualifier?: string;
  /**
   * An optional string to describe the retention policy for a dataset. This field can also be applied more granularly at either the Collection or field level of a Dataset.
   */
  retention?: string;
  /**
   * An optional array of objects that describe hierarchical/nested fields (typically found in NoSQL databases).
   */
  fields?: Array<DatasetField>;
};
