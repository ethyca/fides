/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ManualFieldRequestType } from './ManualFieldRequestType';
import type { ManualTaskFieldType } from './ManualTaskFieldType';

/**
 * Simplified schema for updating a manual field.
 */
export type ManualFieldUpdate = {
  /**
   * Display label for the field
   */
  label: string;
  /**
   * Help text/description for the field
   */
  help_text: string;
  /**
   * Field type (text, attachment, checkbox)
   */
  field_type: ManualTaskFieldType;
  /**
   * Request type this field applies to
   */
  request_type: ManualFieldRequestType;
};

