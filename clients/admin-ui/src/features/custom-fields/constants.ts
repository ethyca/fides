import { ResourceTypes } from "~/types/api";

export const FIELD_TYPE_MAP = new Map([
  ["string", "Single Select"],
  ["string[]", "Multi Select"],
]);

export const RESOURCE_TYPE_MAP = new Map([
  [ResourceTypes.SYSTEM, "system:information"],
  [ResourceTypes.DATA_USE, "taxonomy:data use"],
  [ResourceTypes.DATA_CATEGORY, "taxonomy:data category"],
  [ResourceTypes.DATA_SUBJECT, "taxonomy:data subject"],
  [ResourceTypes.PRIVACY_DECLARATION, "system:data use"],
]);
