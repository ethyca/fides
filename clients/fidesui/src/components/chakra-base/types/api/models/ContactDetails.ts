/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * The contact details information model.
 *
 * Used to capture contact information for controllers, used
 * as part of exporting a data map / ROPA.
 *
 * This model is nested under an Organization and
 * potentially under a system/dataset.
 */
export type ContactDetails = {
  /**
   * An individual name used as part of publishing contact information. Encrypted at rest on the server.
   */
  name?: string;
  /**
   * An individual address used as part of publishing contact information. Encrypted at rest on the server.
   */
  address?: string;
  /**
   * An individual email used as part of publishing contact information. Encrypted at rest on the server.
   */
  email?: string;
  /**
   * An individual phone number used as part of publishing contact information. Encrypted at rest on the server.
   */
  phone?: string;
};
