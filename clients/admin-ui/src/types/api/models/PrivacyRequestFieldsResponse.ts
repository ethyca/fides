/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { NestedFieldDict } from "./NestedFieldDict";
import type { Operator } from "./Operator";

/**
 * Schema for privacy request fields response.
 *
 * The structure is a nested dictionary where leaf nodes are PrivacyRequestFieldDefinition objects.
 * Supports arbitrary nesting depth (e.g., privacy_request.custom_privacy_request_fields.tenant_id).
 */
export type PrivacyRequestFieldsResponse = {
  /**
   * Nested dictionary of available privacy request fields. Leaf nodes are PrivacyRequestFieldDefinition objects.
   */
  privacy_request: NestedFieldDict;
  /**
   * Mapping of data types to their valid operators. Use this to filter operator options based on the selected field's type.
   */
  operator_compatibility: Record<string, Array<Operator>>;
};
