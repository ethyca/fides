import { ResourceTypes } from "~/types/api";

export const RESOURCE_TYPE_MAP = new Map([
  [ResourceTypes.SYSTEM, "system:information"],
  [ResourceTypes.DATA_USE, "taxonomy:data use"],
  [ResourceTypes.DATA_CATEGORY, "taxonomy:data category"],
  [ResourceTypes.DATA_SUBJECT, "taxonomy:data subject"],
  [ResourceTypes.PRIVACY_DECLARATION, "system:data use"],
]);

export enum FieldTypes {
  SINGLE_SELECT = "singleSelect",
  MULTIPLE_SELECT = "multipleSelect",
  OPEN_TEXT = "openText",
}

export const RESOURCE_TYPE_OPTIONS = [
  {
    label: `taxonomy:${ResourceTypes.DATA_CATEGORY}`,
    value: ResourceTypes.DATA_CATEGORY,
  },
  {
    label: `taxonomy:${ResourceTypes.DATA_SUBJECT}`,
    value: ResourceTypes.DATA_SUBJECT,
  },
  {
    label: `taxonomy:${ResourceTypes.DATA_USE}`,
    value: ResourceTypes.DATA_USE,
  },
  {
    label: `${ResourceTypes.SYSTEM}:information`,
    value: ResourceTypes.SYSTEM,
  },
  {
    label: "system:data use",
    value: ResourceTypes.PRIVACY_DECLARATION,
  },
];

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
