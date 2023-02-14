import { ResourceTypes } from "~/types/api";

import { RESOURCE_TYPE_OPTIONS } from "./constants";

export const getResourceType = (valueOrLabel: string) =>
  RESOURCE_TYPE_OPTIONS.find(
    (option) => option.value === valueOrLabel || option.label === valueOrLabel
  )?.value ?? ResourceTypes.SYSTEM;
