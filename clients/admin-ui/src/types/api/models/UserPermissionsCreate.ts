/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { RoleRegistryEnum } from "./RoleRegistryEnum";
import type { ScopeRegistryEnum } from "./ScopeRegistryEnum";

/**
 * Data required to create a FidesUserPermissions record
 *
 * Users will generally be assigned role(s) directly which are associated with many scopes,
 * but we also will continue to support the ability to be assigned specific individual scopes.
 */
export type UserPermissionsCreate = {
  scopes?: Array<ScopeRegistryEnum>;
  roles?: Array<RoleRegistryEnum>;
};
