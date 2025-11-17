/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { IdentityDefinitionType } from "./IdentityDefinitionType";

/**
 * Schema for creating an identity definition.
 */
export type IdentityDefinitionCreate = {
  identity_key: string;
  name: string;
  description?: string | null;
  type: IdentityDefinitionType;
};
