import {
  AllowedTypes,
  CustomFieldDefinitionWithId,
  ResourceTypes,
} from "~/types/api";

export const RESOURCE_TYPE_MAP = new Map([
  [ResourceTypes.SYSTEM, "system:information"],
  [ResourceTypes.DATA_USE, "taxonomy:data use"],
  [ResourceTypes.DATA_CATEGORY, "taxonomy:data category"],
  [ResourceTypes.DATA_SUBJECT, "taxonomy:data subject"],
  [ResourceTypes.PRIVACY_DECLARATION, "system:data use"],
]);

export const getCustomFieldType = (value: CustomFieldDefinitionWithId) => {
  // eslint-disable-next-line no-underscore-dangle
  if (value.field_type === AllowedTypes.STRING_) {
    return "Multi-value select";
  }
  if (value.allow_list_id) {
    return "Single-value select";
  }
  return "Open text";
};
