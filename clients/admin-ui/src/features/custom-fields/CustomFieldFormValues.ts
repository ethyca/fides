import { FieldTypes } from "~/features/custom-fields/constants";
import { CustomFieldDefinition } from "~/types/api";

export interface CustomFieldsFormValues
  extends Omit<CustomFieldDefinition, "field_type"> {
  options?: string[];
  field_type: FieldTypes;
}
