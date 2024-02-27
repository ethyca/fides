/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { RoleRegistryEnum } from "./RoleRegistryEnum";
import type { ScopeRegistryEnum } from "./ScopeRegistryEnum";

/**
 * Response after creating, editing, or retrieving a FidesUserPermissions record.
 *
 * Overrides in Plus to use the Plus ScopeRegistryEnum so Plus scopes are returned.
 */
export type UserPermissionsPlusResponse = {
  roles: Array<RoleRegistryEnum>;
  id: string;
  user_id: string;
  total_scopes: Array<ScopeRegistryEnum>;
};
