import { CustomFieldDefinition } from "~/types/api";

export interface CustomFieldsFormValues
  extends Omit<CustomFieldDefinition, "field_type"> {
  options?: string[];
  field_type?: string;
  template?: string;
  value_type: string;
}

export const CUSTOM_TEMPLATE_VALUE = "create-custom-values";
