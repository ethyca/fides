/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ManualTaskFieldMetadata } from "./ManualTaskFieldMetadata";
import type { ManualTaskFieldType } from "./ManualTaskFieldType";

/**
 * Base schema for all field definitions.
 */
export type ManualTaskFieldBase = {
  /**
   * Unique key for the field
   */
  field_key: string;
  /**
   * Type of the field
   */
  field_type: ManualTaskFieldType;
  /**
   * Field metadata and configuration
   */
  field_metadata: ManualTaskFieldMetadata;
};
