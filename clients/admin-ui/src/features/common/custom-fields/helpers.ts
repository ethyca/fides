import { capitalize } from "~/features/common/utils";
import { ResourceTypes } from "~/types/api";

import { RESOURCE_TYPE_MAP } from "./constants";

export const getResourceType = (value: string) =>
  RESOURCE_TYPE_MAP.has(capitalize(value))
    ? (RESOURCE_TYPE_MAP.get(capitalize(value))!.value as ResourceTypes)
    : ResourceTypes.SYSTEM;
