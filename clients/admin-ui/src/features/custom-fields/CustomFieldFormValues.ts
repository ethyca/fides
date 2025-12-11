import { CustomFieldDefinition } from "~/types/api";

export interface CustomFieldsFormValues
  extends Omit<CustomFieldDefinition, "field_type"> {
  options?: string[];
  field_type?: string;
  value_type: string;
}
