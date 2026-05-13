/* istanbul ignore file */
/* tslint:disable */

export type CustomFieldWithId = {
  resource_id: string;
  custom_field_definition_id: string;
  value: string | Array<string>;
  id?: string | null;
};
