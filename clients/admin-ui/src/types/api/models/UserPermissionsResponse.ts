/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { RoleRegistryEnum } from "./RoleRegistryEnum";
import type { ScopeRegistryEnum } from "./ScopeRegistryEnum";

/**
 * Response after creating, editing, or retrieving a FidesUserPermissions record.
 */
export type UserPermissionsResponse = {
  scopes: Array<ScopeRegistryEnum>;
  roles?: Array<RoleRegistryEnum>;
  id: string;
  user_id: string;
  total_scopes: Array<ScopeRegistryEnum>;
};
