// eslint-disable-next-line import/prefer-default-export
export const DATA_QUALIFIERS = [
  {
    key: "aggregated",
    label: "Aggregated",
    styles: { backgroundColor: "green.500", color: "white" },
  },
  {
    key: "anonymized",
    label: "Anonymized",
    styles: { backgroundColor: "yellow.400", color: "gray.700" },
  },
  {
    key: "aggregated.anonymized",
    label: "Unlinked Pseudonymized",
    styles: { backgroundColor: "orange.300", color: "gray.700" },
  },
  {
    key: "aggregated.anonymized.unlinked_pseudonymized",
    label: "Pseudonymized",
    styles: { backgroundColor: "orange.500", color: "white" },
  },
  {
    key: "aggregated.anonymized.unlinked_pseudonymized.pseudonymized.identified",
    label: "Identified",
    styles: { backgroundColor: "red.600", color: "white" },
  },
];
/**
 * Tooltip copy, from https://ethyca.github.io/fides/1.6.1/language/resources/dataset/
 */

// DATASET
export const DATASET_NAME_TOOLTIP = "A UI-friendly label for the Dataset.";
export const DATASET_DESCRIPTION_TOOLTIP =
  "A human-readable description of the Dataset.";
export const DATASET_RETENTION_TOOLTIP =
  "An optional string to describe the retention policy for a dataset. This field can also be applied more granularly at either the Collection or field level of a Dataset";
export const DATASET_DATA_QUALIFIER_TOOLTIP =
  "Arrays of Data Qualifier resources, identified by fides_key, that apply to all collections in the Dataset.";
export const DATASET_DATA_CATEGORY_TOOLTIP =
  "Arrays of Data Category resources, identified by fides_key, that apply to all collections in the Dataset.";
export const DATASET_THIRD_COUNTRY_TRANSFERS_TOOLTIP =
  "An optional array to identify any third countries where data is transited to. For consistency purposes, these fields are required to follow the Alpha-3 code set in ISO 3166-1";

// DATASET COLLECTION
export const DATASET_COLLECTION_DESCRIPTION_TOOLTIP =
  "A human-readable description of the collection.";
export const DATASET_COLLECTION_DATA_QUALIFIER_TOOLTIP =
  "Arrays of Data Qualifier resources, identified by fides_key, that apply to all fields in the collection.";

export const DATASET_COLLECTION_DATA_CATEGORY_TOOLTIP =
  "Arrays of Data Qualifier resources, identified by fides_key, that apply to all fields in the collection.";

// DATASET FIELD
export const DATASET_FIELD_DESCRIPTION_TOOLTIP =
  "A human-readable description of the field.";
export const DATASET_FIELD_DATA_QUALIFIER_TOOLTIP =
  "A Data Qualifier that applies to this field. Note that this field holds a single value, therefore, the property name is singular.";
export const DATASET_FIELD_DATA_CATEGORY_TOOLTIP =
  "Arrays of Data Categories, identified by fides_key, that applies to this field.";
