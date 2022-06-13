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
