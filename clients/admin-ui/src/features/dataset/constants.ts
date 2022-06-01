// eslint-disable-next-line import/prefer-default-export
export const DATA_QUALIFIERS = [
  { key: "aggregated", label: "Aggregated", color: "green" },
  { key: "anonymized", label: "Anonymized", color: "green" },
  {
    key: "aggregated.anonymized",
    label: "Unlinked Pseudonymized",
    color: "yellow",
  },
  {
    key: "aggregated.anonymized.unlinked_pseudonymized",
    label: "Pseudonymized",
    color: "yellow",
  },
  {
    key: "aggregated.anonymized.unlinked_pseudonymized.pseudonymized.identified",
    label: "Identified",
    color: "red",
  },
];
