import { capitalize } from "~/features/common/utils";
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
    label: `Taxonomy - ${capitalize(ResourceTypes.DATA_CATEGORY)}`,
    value: ResourceTypes.DATA_CATEGORY,
  },
  {
    label: `Taxonomy - ${capitalize(ResourceTypes.DATA_SUBJECT)}`,
    value: ResourceTypes.DATA_SUBJECT,
  },
  {
    label: `Taxonomy - ${capitalize(ResourceTypes.DATA_USE)}`,
    value: ResourceTypes.DATA_USE,
  },
  {
    label: capitalize(ResourceTypes.SYSTEM),
    value: ResourceTypes.SYSTEM,
  },
  {
    label: "System - Data use",
    value: ResourceTypes.PRIVACY_DECLARATION,
  },
];
