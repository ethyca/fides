/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { RoleRegistryEnum } from "./RoleRegistryEnum";
import type { ScopeRegistryEnum } from "./ScopeRegistryEnum";

/**
 * Data required to edit a FidesUserPermissions record.
 */
export type UserPermissionsEdit = {
  scopes?: Array<ScopeRegistryEnum>;
  roles?: Array<RoleRegistryEnum>;
  id?: string;
};
