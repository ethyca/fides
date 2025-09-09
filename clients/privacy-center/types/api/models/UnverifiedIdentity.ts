/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Exclude email and phone number from the identity
 */
export type UnverifiedIdentity = {
  ga_client_id?: string | null;
  ljt_readerID?: string | null;
  fides_user_device_id?: string | null;
  external_id?: string | null;
};
