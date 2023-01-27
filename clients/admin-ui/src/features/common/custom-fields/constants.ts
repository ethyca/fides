import { ItemOption } from "~/features/common/dropdown/types";
import { capitalize } from "~/features/common/utils";
import { AllowedTypes, ResourceTypes } from "~/types/api";

export enum TabTypes {
  CREATE_CUSTOM_FIELDS,
  CREATE_CUSTOM_LISTS,
}

export const FIELD_TYPE_MAP = new Map<string, ItemOption>([
  ["Single select", { value: AllowedTypes.STRING }],
  // eslint-disable-next-line no-underscore-dangle
  ["Multiple select", { value: AllowedTypes.STRING_ }],
]);

export const RESOURCE_TYPE_MAP = new Map<string, ItemOption>([
  [
    capitalize(ResourceTypes.DATA_CATEGORY),
    { value: ResourceTypes.DATA_CATEGORY },
  ],
  [
    capitalize(ResourceTypes.DATA_SUBJECT),
    { value: ResourceTypes.DATA_SUBJECT },
  ],
  [capitalize(ResourceTypes.DATA_USE), { value: ResourceTypes.DATA_USE }],
  [capitalize(ResourceTypes.SYSTEM), { value: ResourceTypes.SYSTEM }],
]);
