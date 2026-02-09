import { LegacyAllowedTypes } from "~/features/common/custom-fields/types";
import {
  FIELD_TYPE_LABEL_MAP,
  FieldTypes,
  TAXONOMY_FIELD_TYPE_LABEL_MAP,
} from "~/features/custom-fields/constants";
import { CustomFieldDefinitionWithId } from "~/types/api";

export const getCustomFieldType = (
  value: CustomFieldDefinitionWithId,
): FieldTypes | string => {
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
  if (fieldType in FIELD_TYPE_LABEL_MAP) {
    return FIELD_TYPE_LABEL_MAP[fieldType as keyof typeof FIELD_TYPE_LABEL_MAP];
  }
  if (fieldType in TAXONOMY_FIELD_TYPE_LABEL_MAP) {
    return TAXONOMY_FIELD_TYPE_LABEL_MAP[
      fieldType as keyof typeof TAXONOMY_FIELD_TYPE_LABEL_MAP
    ];
  }
  return fieldType;
};
