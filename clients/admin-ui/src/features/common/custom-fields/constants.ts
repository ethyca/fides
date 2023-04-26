import { AllowedTypes, ResourceTypes } from "~/types/api";

export enum TabTypes {
  CREATE_CUSTOM_FIELDS,
  CREATE_CUSTOM_LISTS,
  CHOOSE_FROM_LIBRARY,
}

export const FIELD_TYPE_OPTIONS = [
  { label: "Single select", value: AllowedTypes.STRING },
  // eslint-disable-next-line no-underscore-dangle
  { label: "Multiple select", value: AllowedTypes.STRING_ },
];

export enum FieldTypes {
  SINGLE_SELECT = "singleSelect",
  MULTIPLE_SELECT = "multipleSelect",
  OPEN_TEXT = "openText",
}

export const FIELD_TYPE_OPTIONS_NEW = [
  { label: "Single select", value: FieldTypes.SINGLE_SELECT },
  // eslint-disable-next-line no-underscore-dangle
  { label: "Multiple select", value: FieldTypes.MULTIPLE_SELECT },
  { label: "Open Text", value: FieldTypes.OPEN_TEXT },
];

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
