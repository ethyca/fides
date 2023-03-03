/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { RoleRegistry } from "./RoleRegistry";

/**
 * Data required to edit a FidesUserPermissions record.
 */
export type UserPermissionsEdit = {
  scopes?: Array<string>;
  roles?: Array<RoleRegistry>;
  id?: string;
};
