import { LegacyResourceTypes } from "~/features/common/custom-fields/types";

export const RESOURCE_TYPE_MAP = new Map([
  [LegacyResourceTypes.SYSTEM, "system:information"],
  [LegacyResourceTypes.DATA_USE, "taxonomy:data use"],
  [LegacyResourceTypes.DATA_CATEGORY, "taxonomy:data category"],
  [LegacyResourceTypes.DATA_SUBJECT, "taxonomy:data subject"],
  [LegacyResourceTypes.PRIVACY_DECLARATION, "system:data use"],
]);

export enum FieldTypes {
  SINGLE_SELECT = "singleSelect",
  MULTIPLE_SELECT = "multipleSelect",
  OPEN_TEXT = "openText",
}

export const FIELD_TYPE_OPTIONS = [
  { label: "Single select", value: FieldTypes.SINGLE_SELECT },
  { label: "Multiple select", value: FieldTypes.MULTIPLE_SELECT },
  { label: "Open text", value: FieldTypes.OPEN_TEXT },
];

export const FIELD_TYPE_LABEL_MAP: Record<FieldTypes, string> = {
  [FieldTypes.SINGLE_SELECT]: "Single-value select",
  [FieldTypes.MULTIPLE_SELECT]: "Multi-value select",
  [FieldTypes.OPEN_TEXT]: "Open text",
};
