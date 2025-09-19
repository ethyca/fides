import { FieldTypes } from "~/features/common/custom-fields";
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

export const FIELD_TYPE_LABEL_MAP: Record<FieldTypes, string> = {
  [FieldTypes.SINGLE_SELECT]: "Single-value select",
  [FieldTypes.MULTIPLE_SELECT]: "Multi-value select",
  [FieldTypes.LOCATION_SELECT]: "Location select",
  [FieldTypes.OPEN_TEXT]: "Open text",
};

export const getCustomFieldTypeLabel = (value: CustomFieldDefinitionWithId) =>
  FIELD_TYPE_LABEL_MAP[getCustomFieldType(value)];

export const getCustomFieldType = (value: CustomFieldDefinitionWithId) => {
  // eslint-disable-next-line no-underscore-dangle
  if (value.field_type === AllowedTypes.STRING_) {
    return FieldTypes.MULTIPLE_SELECT;
  }
  if (value.allow_list_id) {
    return FieldTypes.SINGLE_SELECT;
  }
  return FieldTypes.OPEN_TEXT;
};
