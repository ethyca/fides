import { Option } from "~/features/common/form/inputs";
import {
  AllowList,
  CustomFieldDefinitionWithId,
  CustomFieldWithId,
} from "~/types/api";

export interface CustomFieldWithIdExtended extends CustomFieldWithId {
  allow_list_id?: string;
}

export interface CustomFieldDefinitionExisting
  extends CustomFieldDefinitionWithId {
  id: string;
}

export interface CustomFieldExisting extends CustomFieldWithId {
  id: string;
}

export interface AllowListWithOptions extends AllowList {
  options: Option[];
}

export type CustomFieldValues = Record<string, string | string[] | undefined>;

/**
 * The custom metadata fields are very dynamic and may not be rendered at all. If they are used,
 * their values are stored as a mapping from the field definition's ID to the value, which may be a
 * string or array depending on the definition's type.
 */
export interface CustomFieldsFormValues {
  fides_key: string;
  /**
   * This is camel-cased because it is only used in UI code and must be handled specially when
   * submitting the form. It does not correspond with a snake-cased API field.
   */
  customFieldValues?: CustomFieldValues;
}
