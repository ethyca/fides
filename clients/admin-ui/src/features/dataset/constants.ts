/**
 * Tooltip copy, from https://ethyca.github.io/fides/1.6.1/language/resources/dataset/
 * These definitions could be expanded to include more metadata about the schema.
 */

export const DATASET = {
  name: { tooltip: "A UI-friendly label for the Dataset." },
  description: { tooltip: "A human-readable description of the Dataset." },
  data_categories: {
    tooltip:
      "Arrays of Data Category resources, identified by fides_key, that apply to all collections in the Dataset.",
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

export const URN_SEPARATOR = "/";
