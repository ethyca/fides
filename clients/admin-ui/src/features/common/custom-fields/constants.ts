import { capitalize } from "~/features/common/utils";
import { AllowedTypes, ResourceTypes } from "~/types/api";

export enum TabTypes {
  CREATE_CUSTOM_FIELDS,
  CREATE_CUSTOM_LISTS,
}

export const FIELD_TYPE_OPTIONS = [
  { label: "Single select", value: AllowedTypes.STRING },
  // eslint-disable-next-line no-underscore-dangle
  { label: "Multiple select", value: AllowedTypes.STRING_ },
];

export const RESOURCE_TYPE_OPTIONS = [
  {
    label: capitalize(ResourceTypes.DATA_CATEGORY),
    value: ResourceTypes.DATA_CATEGORY,
  },
  {
    label: capitalize(ResourceTypes.DATA_SUBJECT),
    value: ResourceTypes.DATA_SUBJECT,
  },
  {
    label: capitalize(ResourceTypes.DATA_USE),
    value: ResourceTypes.DATA_USE,
  },

  {
    label: capitalize(ResourceTypes.SYSTEM),
    value: ResourceTypes.SYSTEM,
  },
];
