/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { PrivacyRequestFieldDefinition } from "./PrivacyRequestFieldDefinition";

/**
 * Schema for nested field dictionary.
 *
 * This is a recursive type that allows for arbitrary nesting depth.
 * Each key can either point to another nested dictionary or a field definition.
 */
export type NestedFieldDict = {
  [key: string]: NestedFieldDict | PrivacyRequestFieldDefinition;
};
