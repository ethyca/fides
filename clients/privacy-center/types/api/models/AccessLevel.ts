/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Perms given to the ConnectionConfig.  For example, with "read" permissions, fidesops promises
 * to not modify the data on a connected application database in any way.
 *
 * "Write" perms mean we can update/delete items in the connected database.
 */
export enum AccessLevel {
  READ = "read",
  WRITE = "write",
}
