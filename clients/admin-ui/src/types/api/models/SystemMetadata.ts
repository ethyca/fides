/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * The SystemMetadata resource model.
 *
 * Object used to hold application specific metadata for a system
 */
export type SystemMetadata = {
  /**
   * The external resource id for the system being modeled.
   */
  resource_id?: string | null;
  /**
   * The host of the external resource for the system being modeled.
   */
  endpoint_address?: string | null;
  /**
   * The port of the external resource for the system being modeled.
   */
  endpoint_port?: string | null;
};
