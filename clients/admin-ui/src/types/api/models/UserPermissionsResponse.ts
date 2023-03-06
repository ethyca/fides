/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { RoleRegistry } from "./RoleRegistry";

/**
 * Response after creating, editing, or retrieving a FidesUserPermissions record.
 */
export type UserPermissionsResponse = {
  scopes?: Array<string>;
  roles?: Array<RoleRegistry>;
  id: string;
  user_id: string;
};
