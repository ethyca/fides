import { FieldActionTypeValue } from "./types";

export const FIELD_ACTION_LABEL: Record<FieldActionTypeValue, string> = {
  approve: "Approve",
  "assign-categories": "Assign categories",
  classify: "Classify",
  promote: "Confirm",
  "un-mute": "Un-mute",
  mute: "Ignore",
};

export const DROPDOWN_OPTIONS: Readonly<FieldActionTypeValue[]> = [
  "classify",
  "approve",
  "promote",
  "mute",
] as const;
