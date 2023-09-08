export const legalBasisForProfilingOptions = [
  "Explicit consent",
  "Contract",
  "Authorised by law",
].map((opt) => ({
  value: opt,
  label: opt,
}));

export const legalBasisForTransferOptions = [
  {
    value: "Adequacy Decision",
    label: "Adequacy decision",
  },
    {
    value: "Supplementary Measures",
    label: "Supplementary measures",
  },
  {
    value: "SCCs",
    label: "Standard contractual clauses",
  },
  {
    value: "BCRs",
    label: "Binding corporate rules",
  },
  {
    value: "Other",
    label: "Other",
  },
];

export const responsibilityOptions = [
  "Controller",
  "Processor",
  "Sub-Processor",
].map((opt) => ({
  value: opt,
  label: opt,
}));
