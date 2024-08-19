/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { RoleRegistryEnum } from "./RoleRegistryEnum";

/**
 * Data required to edit a FidesUserPermissions record.
 */
export type UserPermissionsEdit = {
  roles: Array<RoleRegistryEnum>;
  id?: string | null;
};
