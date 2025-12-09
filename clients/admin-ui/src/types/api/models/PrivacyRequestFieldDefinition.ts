/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Schema for privacy request field definition.
 *
 * This defines the structure of leaf nodes in the nested privacy request fields response.
 */
export type PrivacyRequestFieldDefinition = {
  /**
   * Path to the field
   */
  field_path: string;
  /**
   * Type of the field
   */
  field_type: PrivacyRequestFieldDefinition.field_type;
  /**
   * Description of the field
   */
  description: string;
  /**
   * Whether this is a convenience field for easier access
   */
  is_convenience_field: boolean;
};

export namespace PrivacyRequestFieldDefinition {
  /**
   * Type of the field
   */
  export enum field_type {
    STRING = "string",
    INTEGER = "integer",
    BOOLEAN = "boolean",
    ARRAY = "array",
  }
}
