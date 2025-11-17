/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Status of the database index for an identity definition.
 *
 * - ready: All partition indexes exist and are valid, ready to use
 * - building: All partition indexes exist but PostgreSQL is actively building them (marked invalid)
 * - error: No indexes exist OR partial indexes exist (creation failed or never completed)
 */
export enum IndexStatus {
  READY = "ready",
  BUILDING = "building",
  ERROR = "error",
}
