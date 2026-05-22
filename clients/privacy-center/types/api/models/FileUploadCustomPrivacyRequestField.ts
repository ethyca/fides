/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ConditionGroup } from "./ConditionGroup";
import type { ConditionLeaf } from "./ConditionLeaf";

/**
 * File upload field. ``max_size_bytes`` and ``allowed_file_types``
 * drive client hints and per-field upload enforcement.
 */
export type FileUploadCustomPrivacyRequestField = {
  label: string;
  required?: boolean | null;
  default_value?: string | null;
  hidden?: boolean | null;
  query_param_key?: string | null;
  display_condition?: ConditionLeaf | ConditionGroup | null;
  field_type?: string;
  max_size_bytes?: number;
  allowed_file_types?: Array<string>;
};
