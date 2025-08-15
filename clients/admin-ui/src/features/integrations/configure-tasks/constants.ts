import { ManualFieldRequestType, ManualTaskFieldType } from "~/types/api";

// Label mappings for field types and request types
export const FIELD_TYPE_LABELS: Record<ManualTaskFieldType, string> = {
  [ManualTaskFieldType.TEXT]: "Text",
  [ManualTaskFieldType.CHECKBOX]: "Checkbox",
  [ManualTaskFieldType.ATTACHMENT]: "Attachment",
};

export const REQUEST_TYPE_LABELS: Record<ManualFieldRequestType, string> = {
  [ManualFieldRequestType.ACCESS]: "Access",
  [ManualFieldRequestType.ERASURE]: "Erasure",
};
