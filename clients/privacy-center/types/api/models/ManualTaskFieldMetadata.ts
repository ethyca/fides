/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Base schema for manual task field metadata.
 */
export type ManualTaskFieldMetadata = {
  /**
   * Display label for the field
   */
  label: string;
  /**
   * Whether the field is required
   */
  required?: boolean;
  /**
   * Help text to display with the field
   */
  help_text?: string | null;
  /**
   * List of data uses associated with this field
   */
  data_uses?: Array<string> | null;
};
