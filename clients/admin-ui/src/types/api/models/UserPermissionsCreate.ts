/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { RoleRegistryEnum } from "./RoleRegistryEnum";

/**
 * Data required to create a FidesUserPermissions record
 *
 * Users will be assigned role(s) directly which are associated with a list of scopes. Scopes
 * cannot be assigned directly to users.
 */
export type UserPermissionsCreate = {
  roles: Array<RoleRegistryEnum>;
};
