/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * A base template for all other Fides Schemas to inherit from.
 */
export type SecurityApplicationConfig = {
  /**
   * A list of client addresses allowed to communicate with the Fides webserver.
   */
  cors_origins?: Array<string>;
};
