/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ConditionGroup } from "./ConditionGroup";
import type { ConditionLeaf } from "./ConditionLeaf";

/**
 * Regular custom privacy request field supporting text, select, multiselect,
 * checkbox, checkbox_group, and textarea types
 */
export type fides__api__schemas__privacy_center_config__CustomPrivacyRequestField =
  {
    label: string;
    required?: boolean | null;
    default_value?: string | null;
    hidden?: boolean | null;
    query_param_key?: string | null;
    display_condition?: ConditionLeaf | ConditionGroup | null;
    field_type?:
      | "text"
      | "select"
      | "multiselect"
      | "checkbox"
      | "checkbox_group"
      | "textarea"
      | null;
    options?: Array<string> | null;
  };
