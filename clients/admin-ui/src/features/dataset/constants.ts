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
 * These definitions could be expanded to include more metadata about the schema.
 */

export const DATASET = {
  name: { tooltip: "A UI-friendly label for the Dataset." },
  description: { tooltip: "A human-readable description of the Dataset." },
  retention: {
    tooltip:
      "An optional string to describe the retention policy for a dataset. This field can also be applied more granularly at either the Collection or field level of a Dataset",
  },
  data_qualifiers: {
    tooltip:
      "Arrays of Data Qualifier resources, identified by fides_key, that apply to all collections in the Dataset.",
  },
  data_categories: {
    tooltip:
      "Arrays of Data Category resources, identified by fides_key, that apply to all collections in the Dataset.",
  },
  third_country_transfers: {
    tooltip:
      "An optional array to identify any third countries where data is transited to. For consistency purposes, these fields are required to follow the Alpha-3 code set in ISO 3166-1",
  },
};

export const COLLECTION = {
  description: { tooltip: "A human-readable description of the collection." },
  data_qualifiers: {
    tooltip:
      "Arrays of Data Qualifier resources, identified by fides_key, that apply to all fields in the collection.",
  },
  data_categories: {
    tooltip:
      "Arrays of Data Category resources, identified by fides_key, that apply to all fields in the collection.",
  },
};

export const FIELD = {
  description: {
    tooltip: "A human-readable description of the field.",
  },
  data_qualifier: {
    tooltip:
      "A Data Qualifier that applies to this field. Note that this field holds a single value, therefore, the property name is singular.",
  },
  data_categories: {
    tooltip:
      "Arrays of Data Category resources, identified by fides_key, that apply to this field.",
  },
};
