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
  data_categories: {
    tooltip:
      "Arrays of Data Category resources, identified by fides_key, that apply to all fields in the collection.",
  },
};

export const FIELD = {
  description: {
    tooltip: "A human-readable description of the field.",
  },
  data_categories: {
    tooltip:
      "Arrays of Data Category resources, identified by fides_key, that apply to this field.",
  },
};
