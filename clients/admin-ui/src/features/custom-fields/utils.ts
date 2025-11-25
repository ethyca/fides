import { LegacyAllowedTypes } from "~/features/common/custom-fields/types";
import {
  FIELD_TYPE_LABEL_MAP,
  FieldTypes,
} from "~/features/custom-fields/constants";
import { CustomFieldDefinitionWithId } from "~/types/api";

export const getCustomFieldType = (
  value: CustomFieldDefinitionWithId,
): FieldTypes | string => {
  // eslint-disable-next-line no-underscore-dangle
  if (value.field_type === LegacyAllowedTypes.STRING_ARRAY) {
    return FieldTypes.MULTIPLE_SELECT;
  }
  if (value.allow_list_id) {
    return FieldTypes.SINGLE_SELECT;
  }
  if (value.field_type === LegacyAllowedTypes.STRING) {
    return FieldTypes.OPEN_TEXT;
  }
  return value.field_type;
};

export const getCustomFieldTypeLabel = (value: CustomFieldDefinitionWithId) => {
  const fieldType = getCustomFieldType(value);
  if (
    fieldType === FieldTypes.OPEN_TEXT ||
    fieldType === FieldTypes.SINGLE_SELECT ||
    fieldType === FieldTypes.MULTIPLE_SELECT
  ) {
    return FIELD_TYPE_LABEL_MAP[fieldType];
  }
  return fieldType;
};
