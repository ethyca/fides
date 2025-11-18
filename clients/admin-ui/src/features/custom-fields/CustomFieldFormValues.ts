import { CustomFieldDefinition } from "~/types/api";

export interface CustomFieldsFormValues extends CustomFieldDefinition {
  options?: string[];
  value_type: string;
}
