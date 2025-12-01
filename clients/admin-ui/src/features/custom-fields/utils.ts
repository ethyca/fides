import {
  FIELD_TYPE_LABEL_MAP,
  FieldTypes,
} from "~/features/custom-fields/constants";
import { AllowedTypes, CustomFieldDefinitionWithId } from "~/types/api";

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

export const getCustomFieldTypeLabel = (value: CustomFieldDefinitionWithId) =>
  FIELD_TYPE_LABEL_MAP[getCustomFieldType(value)];
