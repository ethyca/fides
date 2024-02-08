/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * A base template for all other Fides Schemas to inherit from.
 */
export type SecurityApplicationConfig = {
  /**
   * A list of HTTP origins allowed to communicate with the Fides webserver.
   */
  cors_origins?: Array<string>;
  /**
   * An optional regex to allowlist wider patterns of HTTP origins to communicate with the Fides webserver.
   */
  cors_origin_regex?: string;
};
